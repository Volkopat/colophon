# Claims map: every claim, its ledger row, and the artefact that carries it

Generated 2026-08-03T15:27:42Z by `python -m colophon.claims_map`. Snapshot: **297 ledger rows**, 255 files under
`results/`, 210 of them scanned as possible carriers.

Parallel tracks write into `results/` while this runs, so the map describes the
repository at the timestamp above. A regeneration that differs is explained by
the timestamp before it is read as drift.

Status counts in this snapshot: DERIVED 19, LITERATURE 11, MEASURED 184, PENDING 25, RETIRED 8, VERIFIED 50.

## How to read this

Three legs. A claim id, the ledger row that states it, and the artefact a reader
opens to check it. `source_file` is the artefact the row itself names.
`carried_by` is every file under `results/` that names the claim id in its own
text, which is a different and weaker thing: a write-up can rest on a number
without ever naming the row it came from.

The third leg is `results/manuscript/`, which holds 24 file(s): `absence_claims.csv`, `absence_claims.md`, `abstract.md`, `abstract_venue.md`, `citation_check.json`, `discussion.md`, `figures.md`, `front_matter.md`, `introduction.md`, `methods.md`, `references.md`, `references_crossref.json`, `results.md`, `table1.csv`, `table1_writers.csv`, `table1_writers.md`, `table2.csv`, `table2_floor_set.csv`, `table2_floor_set.md`, `table3.csv`, `table4.csv`, `table5.csv`, `table6.csv`, `tables.md`. **65 of the 297 claim ids are
named inside it.** The rest are carried by a results write-up or by a CSV table
and have no manuscript location yet. Files there whose name marks them as a
numbered table or figure: `table1.csv`, `table1_writers.csv`, `table1_writers.md`, `table2.csv`, `table2_floor_set.csv`, `table2_floor_set.md`, `table3.csv`, `table4.csv`, `table5.csv`, `table6.csv`. A claim named in one of those has a table to point
at, a claim named only in the prose has a section, and the `carried by` column
says which, per row.

Two exclusions, stated because they change the counts. `results/ledger.csv` and
this map's own two outputs are not scanned as carriers: they name every id by
construction and would report full coverage whatever the write-ups say.
`results/pending_ledger/` is not scanned and not counted as an uncited artefact,
because a proposed row is a ledger draft rather than evidence.

Claims are quoted truncated, never in full, so a retired wording cannot re-enter
prose through the file that lists it.

## The map

| id | section | status | claim | source_file | source | carried by, id named in |
|---|---|---|---|---|---|---|
| P0-01 | P0 | MEASURED | The IDC v24 index holds one row per series, 1,032,911 se ... | results/phase0/census_all.csv | yes | (nothing) |
| P0-02 | P0 | MEASURED | Derived objects, defined as the nine SOP classes listed ... | results/phase0/census_derived.csv | yes | (nothing) |
| P0-03 | P0 | MEASURED | Segmentation Storage is the largest derived class by vol ... | results/phase0/census_derived.csv | yes | (nothing) |
| P0-04 | P0 | MEASURED | Every derived series in IDC v24 is Explicit VR Little En ... | results/phase0/transfer_syntax.csv | yes | results/pre06_sampling_frame.md |
| P0-05 | P0 | MEASURED | IDC v24 holds 1,086 Grayscale Softcopy Presentation Stat ... | results/phase0/gsps_split.csv | yes | results/phase2/net_rates_gsps.md |
| P0-06 | P0 | MEASURED | Parametric Map holdings are 691 series, all in collectio ... | results/phase0/parametric_map.csv | yes | (nothing) |
| P0-07 | P0 | MEASURED | Every derived series in IDC v24 carries a Creative Commo ... | results/phase0/licenses.csv | yes | (nothing) |
| P0-08 | P0 | MEASURED | The six classes the brief calls exhaustively downloadabl ... | results/phase0/phase2_budget.csv | yes | (nothing) |
| P0-09 | P0 | MEASURED | Phase 0 samples nothing. It aggregates the complete inde ... | results/phase0_census.md and results/phase0/*.csv | yes | (nothing) |
| P0-12 | P0 | PENDING | This census covers non-image derived SOP classes only. O ... | (none) | none named | results/pre06_sampling_frame.md |
| P0-10 | P0 | MEASURED | Two denominators are carried throughout: derived objects ... | results/phase0/census_by_analysis_result.csv | yes | (nothing) |
| P0-11 | P0 | MEASURED | Per-series rather than per-instance validation would mis ... | results/phase0/first_file_coverage.csv | yes | results/pre06_sampling_frame.md |
| C3-01 | C3 | MEASURED | Manufacturer and ManufacturerModelName are populated on ... | results/phase0/provenance_population_by_sop.csv | yes | (nothing) |
| C3-02 | C3 | MEASURED | Declared equipment identity across the derived populatio ... | results/phase0/provenance_buckets.csv | yes | (nothing) |
| C3-03 | C3 | MEASURED | IDC already applies a convention that names the producin ... | results/phase0/provenance_converter_pairs.csv | yes | (nothing) |
| C3-11 | C3 | MEASURED | The largest single analysis result in the archive declar ... | results/phase0/provenance_name_agreement.csv | yes | results/ai_use.md; results/manuscript/tables.md; results/submission/04_tables.md |
| C3-10 | C3 | MEASURED | Several incompatible conventions for declaring equipment ... | results/phase0/provenance_conventions.csv | yes | (nothing) |
| C3-04 | C3 | MEASURED | A single encoding tool is declared under several distinc ... | results/phase0/provenance_spelling_variants.csv | yes | (nothing) |
| C3-05 | C3 | MEASURED | For most large analysis results the declared equipment s ... | results/phase0/provenance_name_agreement.csv | yes | (nothing) |
| C3-06 | C3 | PENDING | ImplementationVersionName (0002,0013), ContributingEquip ... | results/claim3_provenance.md and results/phase0/provenance_*.csv | yes | (nothing) |
| C3-07 | C3 | MEASURED | A measurable share of derived series declare an equipmen ... | results/phase0/provenance_acquisition_inheritance.csv | yes | (nothing) |
| C3-08 | C3 | MEASURED | Claim 3 at Phase 0 samples nothing ... | results/claim3_provenance.md and results/phase0/provenance_*.csv | yes | (nothing) |
| C3-12 | C3 | MEASURED | Series in this archive are not independent observations. ... | results/phase0/provenance_by_collection.csv | yes | results/phase2/net_rates_comprehensive_3d_sr.md; results/phase2/net_rates_comprehensive_sr.md; results/pre06_sampling_frame.md |
| C3-13 | C3 | MEASURED | The series-weighted encoder rate is substantially attrib ... | results/phase0/provenance_leave_one_out.csv | yes | results/pre06_sampling_frame.md |
| C3-14 | C3 | PENDING | The normative yardstick for claim 3 is PS3.3 Final Text, ... | (none) | none named | (nothing) |
| C3-06-air | C3 | RETIRED | The IHE AI Results profile section 6.5.3.1 is the normat ... | (none) | none named | (nothing) |
| C3-15 | C3 | MEASURED | Scoring is semantic, not presence-based, and absent, emp ... | results/sentinels.json | yes | (nothing) |
| C3-02-prev | C3 | RETIRED | The majority of derived series declare a general purpose ... | (none) | none named | (nothing) |
| C3-09 | C3 | PENDING | De-identification is a confounder on any absence-based p ... | results/claim3_provenance.md and results/phase0/provenance_*.csv | yes | (nothing) |
| PA-01 | PA | LITERATURE | No publication measures conformance or provenance of AI- ... | results/prior_art.md | yes | results/prisma_s_appendix.md |
| PA-02 | PA | LITERATURE | Three works partially occupy adjacent ground and must be ... | results/prior_art.md | yes | (nothing) |
| PA-03 | PA | LITERATURE | Validation of public DICOM archives is a documented, rou ... | results/prior_art.md | yes | results/ai_use.md |
| PA-03-prev | PA | RETIRED | The published state of the art in validating a public DI ... | results/prior_art.md | yes | (nothing) |
| PA-08 | PA | PENDING | The genuinely uncovered ground is warnings. Existing col ... | results/prior_art.md | yes | results/prisma_s_appendix.md |
| PA-09 | PA | PENDING | The denominators this study reports already exist inside ... | results/prior_art.md | yes | results/prisma_s_appendix.md |
| PA-04 | PA | LITERATURE | No public corpus of clinical or archive-derived GSPS obj ... | results/prior_art.md | yes | (nothing) |
| PA-05 | PA | RETIRED | The brief's characterisation of the peer-reviewed GSPS l ... | results/prior_art.md | yes | results/ai_use.md |
| PA-06 | PA | LITERATURE | Claim 2 is a measurement of an acknowledged phenomenon, ... | results/prior_art.md | yes | results/ai_use.md |
| PA-07 | PA | PENDING | A manual pass over Google Scholar, Scopus, Web of Scienc ... | results/prior_art.md | yes | results/prior_art_recheck.md; results/prisma_s_appendix.md; results/prisma_s_rows.csv |
| W-01 | W | MEASURED | A writer census over the derived population, needed befo ... | results/phase0/writer_census.csv | yes | results/pre06_sampling_frame.md |
| W-02 | W | MEASURED | Producer identity for the largest analysis result is rec ... | results/phase0/carrier_hierarchy.csv | yes | (nothing) |
| W-03 | W | MEASURED | Unstable declared spellings cause measurable recall loss ... | results/phase0/cohort_recall.json | yes | (nothing) |
| W-04 | W | MEASURED | A published sentinel list is required, because the attri ... | results/sentinels.json | yes | (nothing) |
| V-01 | V | MEASURED | The panel has two axes. Axis 1 is conformance, scored by ... | results/panel.json | yes | (nothing) |
| V-02 | V | MEASURED | Axis 2 is asymmetric and informative only on failure, be ... | results/panel.json | yes | (nothing) |
| V-03 | V | MEASURED | PixelMed DicomSRValidator is in the panel for all struct ... | results/panel.json | yes | (nothing) |
| V-04 | V | PENDING | The PixelMed jar is not yet present in the pinned toolch ... | results/panel.json | yes | results/manuscript/methods.md; results/manuscript/references.md; results/manuscript/results.md; results/phase3_segmentation.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| V-05 | V | MEASURED | pydicom-seg is excluded from the panel and the reason is ... | results/panel.json | yes | results/ai_use.md |
| V-06 | V | VERIFIED | Panel independence is declared rather than assumed. Two ... | results/panel.json | yes | results/manuscript/methods.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| V-07 | V | MEASURED | The dcmqi readers are pinned at the build installed in t ... | results/panel.json | yes | (nothing) |
| V-08 | V | MEASURED | The panel is not uniform across SOP classes and is never ... | results/panel.json | yes | (nothing) |
| V-09 | V | MEASURED | Every tool considered and excluded is listed with a stat ... | results/panel.json | yes | (nothing) |
| V-10 | V | PENDING | Two parts of the panel are weak and are declared weak in ... | results/panel.json | yes | (nothing) |
| PRE-02 | V | PENDING | Writer-aware scoring. Every axis-2 result is labelled IN ... | results/panel.json | yes | results/table1_writers.md |
| PRE-03 | V | PENDING | Claim 2 adjudication rule. Where validators disagree, th ... | results/panel.json | yes | results/ai_use.md; results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/methods.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| PRE-04 | V | PENDING | Standard-edition control. One edition is pinned, dicom-v ... | results/panel.json | yes | results/adjudication2/two_pass_comparison.csv; results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/methods.md; results/manuscript/references.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| PRE-05 | V | PENDING | Claim 1 threshold, set before the data. PRE-01 predicted ... | results/phase2/net_rates_rwv_kos.md, results/phase2/net_rates_gsps.md, results/phase2/net_rates_parametric_map.md, results/phase2/net_rates_comprehensive_sr.md, results/phase2/net_rates_comprehensive_3d_sr.md, results/phase2/net_rates_comprehensive_3d_sr.md | yes | results/manuscript/results.md; results/manuscript/tables.md; results/phase2/adjudication_gsps.csv; results/phase2/net_rates_comprehensive_3d_sr.md; results/phase2/net_rates_comprehensive_sr.md; results/phase2/net_rates_gsps.md; results/phase2/net_rates_parametric_map.md; results/phase2/net_rates_rwv_kos.md; results/pre06_sampling_frame.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md |
| PRE-06 | V | MEASURED | Sampling frame, fixed before seeing which strata look in ... | results/phase3_segmentation.md | yes | results/ai_use.md; results/cp/README.md; results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/methods.md; results/manuscript/results.md; results/manuscript/table1.csv; results/manuscript/tables.md; results/phase3_segmentation.md; results/pre06_sampling_frame.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md |
| PRE-07 | V | PENDING | Manual verification sample. The panel is entirely automa ... | results/panel.json | yes | results/manuscript/methods.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| PRE-01 | PRE | RETIRED | Pre-registered prediction. Claim 1 will return largely n ... | results/phase2/net_rates_rwv_kos.md | yes | results/ai_use.md; results/manuscript/methods.md; results/manuscript/results.md; results/phase2/net_rates_comprehensive_3d_sr.md; results/phase2/net_rates_comprehensive_sr.md; results/phase2/net_rates_gsps.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| STD-01 | STD | VERIFIED | The Algorithm Identification Macro has six attributes. T ... | results/standards.json | yes | results/typecheck/type_reverification.csv |
| STD-02 | STD | VERIFIED | SegmentationAlgorithmIdentificationSequence (0062,0007) ... | results/standards.json | yes | results/phase3_segmentation.md; results/typecheck/type_reverification.csv |
| STD-02-hyp | STD | RETIRED | Segmentation objects declaring SegmentAlgorithmType AUTO ... | results/standards.json | yes | (nothing) |
| STD-03 | STD | VERIFIED | Two conformance hooks survive in the Segmentation IOD an ... | results/standards.json | yes | results/ihe_air_table.md; results/standards.json; results/typecheck/type_reverification.csv |
| STD-04 | STD | VERIFIED | Enhanced General Equipment is Mandatory in the Segmentat ... | results/standards.json | yes | results/figures/manifest.json; results/ihe_air_table.md; results/manuscript/figures.md; results/manuscript/methods.md; results/manuscript/tables.md; results/standards.json; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md; results/typecheck/type_reverification.csv |
| STD-05 | STD | MEASURED | Results are reported in three grades, never two: non-con ... | results/standards.json | yes | (nothing) |
| STD-06 | STD | VERIFIED | IHE AIR imposes an unconditional shall on the Creator to ... | results/standards.json | yes | results/ihe_air_table.md; results/standards.json |
| STD-06-untested | STD | RETIRED | IHE AIR has no Connectathon test case and no Gazelle tes ... | results/standards.json | yes | (nothing) |
| F1-01 | F1 | MEASURED | The validator floor is writer-specific. On the only clas ... | results/floor_set.csv | yes | results/manuscript/methods.md; results/manuscript/results.md; results/manuscript/tables.md; results/pre06_sampling_frame.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md |
| F1-02 | F1 | MEASURED | A conformant highdicom Segmentation draws zero dciodvfy ... | results/floor_set.csv | yes | (nothing) |
| F1-03 | F1 | MEASURED | The two validators disagree about whether the floor tran ... | results/floor_set.csv | yes | results/manuscript/tables.md; results/submission/04_tables.md |
| F1-04 | F1 | MEASURED | dcmqi could not emit two of the four nominated shared cl ... | results/floor_set.csv | yes | (nothing) |
| F1-05 | F1 | MEASURED | The two writers place TID 1500 in different SOP classes, ... | results/floor_set.csv | yes | results/manuscript/table2_floor_set.md |
| F1-06 | F1 | MEASURED | dciodvfy exit status is not a verdict. Every object in t ... | results/floor_set.csv | yes | (nothing) |
| F1-07 | F1 | MEASURED | The registered message-matching rule is incomplete and w ... | results/floor_set.csv | yes | (nothing) |
| F1-08 | F1 | PENDING | Two registered tool pins are not satisfied on this machi ... | results/floor_set.csv | yes | (nothing) |
| F1-09 | F1 | MEASURED | Content was held equal across writers and verified befor ... | results/floor_set.csv | yes | (nothing) |
| P2P-01 | P2P | MEASURED | Pilot of ten dcmqi-written Segmentation series from IDC, ... | results/phase2/pilot_provenance.csv | yes | (nothing) |
| P2P-02 | P2P | MEASURED | The dcmqi ClinicalTrialSeries message class seen on the ... | results/phase2/pilot_message_classes.csv | yes | (nothing) |
| P2P-03 | P2P | MEASURED | Message classes observed across the pilot, by validator ... | results/phase2/pilot_message_classes.csv | yes | (nothing) |
| P2P-04 | P2P | MEASURED | SoftwareVersions (0018,1020) captured verbatim in three ... | results/phase2/pilot_provenance.csv | yes | (nothing) |
| P2P-05 | P2P | MEASURED | File-meta identification names the encoding library's ow ... | results/phase2/pilot_provenance.csv | yes | results/manuscript/tables.md; results/submission/04_tables.md |
| P2P-08 | P2P | MEASURED | A minority of objects declaring dcmqi in the equipment a ... | results/phase2/pilot_provenance.csv | yes | results/manuscript/table1_writers.md |
| P2P-09 | P2P | MEASURED | SoftwareVersions on dcmqi-written corpus objects is an a ... | results/phase2/pilot_provenance.csv | yes | results/manuscript/tables.md; results/submission/04_tables.md |
| P2P-06 | P2P | MEASURED | ContributingEquipmentSequence (0018,A001) on dcmqi-writt ... | results/phase2/pilot_provenance.csv | yes | (nothing) |
| P2P-07 | P2P | MEASURED | s5cmd was used to fetch rather than the AWS CLI, which i ... | results/phase2/pilot_fetch_log.csv | yes | (nothing) |
| F1-03-prev | F1 | RETIRED | dicom-validator returns an identical six-class set for b ... | results/floor_set.csv | yes | results/manuscript/table2_floor_set.md |
| F1-10 | F1 | MEASURED | A parser defect in this project silently dropped a class ... | results/floor_set.csv | yes | results/manuscript/table2_floor_set.md |
| P2C-01 | P2C | PENDING | Phase 2 census of the eight non-Segmentation derived cla ... | results/phase2/census_rates.csv | yes | results/manuscript/tables.md; results/submission/04_tables.md |
| P2C-02 | P2C | MEASURED | Gross error-class and warning-class rates by SOP class a ... | results/phase2/census_message_classes.csv | yes | results/phase2/net_rates_gsps.md |
| P2C-03 | P2C | MEASURED | Provenance carriers are reported in three states, and ze ... | results/phase2/census_provenance_states.csv | yes | (nothing) |
| P2C-04 | P2C | MEASURED | dcmpschk reports its own success line with a severity pr ... | results/phase2/census_message_classes.csv | yes | results/phase2/net_rates_gsps.md |
| B-01 | B1 | MEASURED | The Phase 1 headline reproduces under the variant harnes ... | results/phase1_variants.csv | yes | (nothing) |
| B-02 | B1 | MEASURED | The two writers' dciodvfy floor sets on SEG BINARY are n ... | results/phase1_variants.csv | yes | results/figures/manifest.json; results/manuscript/figures.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md |
| B-03 | B1 | MEASURED | The dicom-validator floor sets on SEG BINARY stay unequa ... | results/phase1_variants.csv | yes | results/figures/manifest.json; results/manuscript/figures.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md |
| B-04 | B1 | MEASURED | No variant flips the direction of the finding ... | results/phase1_variants.csv | yes | (nothing) |
| B-05 | B1 | MEASURED | Deflated Explicit VR Little Endian is not read by the pi ... | results/phase1_variants.csv | yes | results/figures/manifest.json; results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/figures.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md |
| B-06 | B1 | MEASURED | Two of the nine variants are Segmentation-only by defini ... | results/phase1_variants.csv | yes | (nothing) |
| B-07 | B1 | MEASURED | The round-trip control shows the pydicom re-save the lad ... | results/phase1_variants.csv | yes | (nothing) |
| B-08 | B1 | MEASURED | SEG FRACTIONAL and Parametric Map carry no between-write ... | results/phase1_variants.csv | yes | (nothing) |
| B-09 | B1 | MEASURED | The TID 1500 SR cell cannot test the direction of the fi ... | results/phase1_variants.csv | yes | (nothing) |
| B-10 | B1 | MEASURED | The writer-specific residue is the stable quantity in th ... | results/phase1_variants.csv | yes | results/figures/manifest.json; results/manuscript/figures.md; results/manuscript/methods.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md |
| B-11 | B1 | PENDING | The ladder inherits the two unsatisfied tool pins from P ... | results/phase1_variants.csv | yes | (nothing) |
| C-CSR-01 | C-CSR | VERIFIED | Referenced Frame Number (0008,1160) present in an SR IMA ... | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | yes | (nothing) |
| C-CSR-02 | C-CSR | VERIFIED | dicom-validator does not independently confirm the Refer ... | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | yes | (nothing) |
| C-CSR-03 | C-CSR | VERIFIED | Coding Scheme Designator SRT is a deprecation notice wit ... | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | yes | (nothing) |
| C-CSR-04 | C-CSR | VERIFIED | Referenced SOP Instances that appear in the SR Content T ... | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | yes | (nothing) |
| C-CSR-05 | C-CSR | MEASURED | dciodvfy error triple for Comprehensive SR Storage, afte ... | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | yes | (nothing) |
| C-CSR-06 | C-CSR | MEASURED | dicom-validator error triple for Comprehensive SR Storag ... | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | yes | (nothing) |
| C-CSR-07 | C-CSR | MEASURED | dciodvfy warning triple for Comprehensive SR Storage, af ... | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | yes | (nothing) |
| C-CSR-08 | C-CSR | MEASURED | Net rate across both validators for Comprehensive SR Sto ... | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | yes | (nothing) |
| C-CSR-09 | C-CSR | MEASURED | Collection-level net rates for Comprehensive SR Storage, ... | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | yes | (nothing) |
| C-CSR-10 | C-CSR | MEASURED | Three NET rules in this class cite PS3.5 or PS3.6 rather ... | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | yes | (nothing) |
| C-CSR-11 | C-CSR | DERIVED | PRE-01 is not recorded as a wrong prediction on the evid ... | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | yes | (nothing) |
| C-GSPS-01 | P2A | MEASURED | Adjudicated against the DICOM standard, every Error-seve ... | results/phase2/net_rates_gsps.md | yes | (nothing) |
| C-GSPS-02 | P2A | MEASURED | Every Warning-severity finding dciodvfy raises on the co ... | results/phase2/net_rates_gsps.md | yes | (nothing) |
| C-GSPS-03 | P2A | MEASURED | dicom-validator raised no finding of any severity on any ... | results/phase2/net_rates_gsps.md | yes | (nothing) |
| C-GSPS-04 | P2A | VERIFIED | dciodvfy's Error on a missing Laterality (0020,0060) in ... | results/phase2/adjudication_gsps.csv | yes | (nothing) |
| C-GSPS-05 | P2A | VERIFIED | dciodvfy's "Missing attribute or value that would be nee ... | results/phase2/adjudication_gsps.csv | yes | (nothing) |
| C-GSPS-06 | P2A | VERIFIED | dciodvfy's "Value dubious for this VR, Retired Person Na ... | results/phase2/adjudication_gsps.csv | yes | (nothing) |
| C-GSPS-07 | P2A | VERIFIED | dciodvfy's DisplayedAreaSelectionSequence ordering check ... | results/phase2/net_rates_gsps.md | yes | (nothing) |
| C-GSPS-08 | P2A | MEASURED | Collection-level net Error rates for the Grayscale Softc ... | results/phase2/net_rates_gsps.md | yes | (nothing) |
| C-GSPS-09 | P2A | DERIVED | Evaluated against PRE-05, the Grayscale Softcopy Present ... | results/phase2/net_rates_gsps.md | yes | (nothing) |
| C-GSPS-10 | P2A | DERIVED | The dcmpschk column is excluded from the Grayscale Softc ... | results/phase2/net_rates_gsps.md | yes | (nothing) |
| C-GSPS-11 | P2A | VERIFIED | Two pin records in this project disagree about which edi ... | results/phase2/adjudication_gsps.csv | yes | (nothing) |
| C-PM-01 | P2C-C | MEASURED | Every distinct validator message class recorded against ... | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | no | (nothing) |
| C-PM-02 | P2C-C | VERIFIED | For the Parametric Map IOD, Values 3 and 4 of Image Type ... | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | no | (nothing) |
| C-PM-03 | P2C-C | VERIFIED | The five Shared Functional Groups sequences dicom-valida ... | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | no | (nothing) |
| C-PM-04 | P2C-C | VERIFIED | Rows (0028,0010) and Columns (0028,0011) are required in ... | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | no | (nothing) |
| C-PM-05 | P2C-C | MEASURED | After adjudication, the entire Parametric Map Storage fa ... | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | no | (nothing) |
| C-PM-06 | P2C-C | MEASURED | No message class recorded against Parametric Map Storage ... | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | no | (nothing) |
| C-PM-07 | P2C-C | MEASURED | The dciodvfy Laterality Type 2C error, which appears on ... | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | no | (nothing) |
| C-PM-08 | P2C-C | MEASURED | The Phase 1 floor set and the archive message classes ov ... | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | no | (nothing) |
| C-PM-09 | P2C-C | DERIVED | Evaluated against PRE-05, Parametric Map Storage falls i ... | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | no | results/phase2/net_rates_parametric_map.md |
| C-RWV-01 | P2C | MEASURED | Real World Value Mapping Storage has no net error class. ... | results/phase2/net_rates_rwv_kos.md | yes | (nothing) |
| C-RWV-02 | P2C | MEASURED | Real World Value Mapping Storage has no net warning clas ... | results/phase2/net_rates_rwv_kos.md | yes | (nothing) |
| C-RWV-03 | P2C | MEASURED | dicom-validator emitted no finding of any severity on an ... | results/phase2/net_rates_rwv_kos.md | yes | (nothing) |
| C-RWV-04 | P2C | VERIFIED | The dciodvfy error class on every Real World Value Mappi ... | results/phase2/adjudication_rwv_kos.csv | yes | (nothing) |
| C-RWV-05 | P2C | VERIFIED | The two coding scheme warnings on Real World Value Mappi ... | results/phase2/adjudication_rwv_kos.csv | yes | (nothing) |
| C-RWV-06 | P2C | VERIFIED | The dciodvfy DICOMDIR warning, raised on every object of ... | results/phase2/adjudication_rwv_kos.csv | yes | (nothing) |
| C-RWV-07 | P2C | VERIFIED | The Retired Person Name form warning is a plausibility c ... | results/phase2/adjudication_rwv_kos.csv | yes | (nothing) |
| C-KOS-01 | P2C | MEASURED | Every Key Object Selection Document object in IDC v24 ca ... | results/phase2/net_rates_rwv_kos.md | yes | (nothing) |
| C-KOS-02 | P2C | MEASURED | dicom-validator reaches the same net finding on the same ... | results/phase2/net_rates_rwv_kos.md | yes | (nothing) |
| C-KOS-03 | P2C | MEASURED | Key Object Selection Document Storage has no net warning ... | results/phase2/net_rates_rwv_kos.md | yes | (nothing) |
| C-KOS-04 | P2C | VERIFIED | Manufacturer (0008,0070) is Type 2 in the General Equipm ... | results/phase2/adjudication_rwv_kos.csv | yes | (nothing) |
| C-RWV-08 | P2C | DERIVED | Real World Value Mapping Storage does not meet the PRE-0 ... | results/phase2/net_rates_rwv_kos.md | yes | (nothing) |
| C-KOS-05 | P2C | DERIVED | Key Object Selection Document Storage meets the PRE-05 t ... | results/phase2/net_rates_rwv_kos.md | yes | (nothing) |
| D-01 | P2D | MEASURED | dcmpschk passes every Grayscale Softcopy Presentation St ... | results/phase2/gsps_dcmpschk.csv | yes | results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| D-02 | P2D | MEASURED | The census recorded a dcmpschk pass as a warning class o ... | results/phase2/census_message_classes.csv | yes | (nothing) |
| D-03 | P2D | MEASURED | dcmpschk's banner line names its input file, and counted ... | results/phase2/gsps_dcmpschk.csv | yes | (nothing) |
| D-04 | P2D | MEASURED | On the same GSPS objects the three validators do not agr ... | results/phase2/gsps_dcmpschk.csv, results/phase2/census_message_classes.csv | yes | results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| E-01 | V | MEASURED | Segmentation Storage partitions into 21 strata by writin ... | results/phase0/seg_strata.csv | yes | (nothing) |
| E-02 | V | DERIVED | The registered minimum of n = 384 is carried from PRE-05 ... | results/pre06_sampling_frame.md | yes | (nothing) |
| E-03 | V | MEASURED | The stratification absorbs the C3-12 provenance clusteri ... | results/phase0/seg_icc_proxies.csv | yes | (nothing) |
| E-04 | V | DERIVED | A post-floor failure rate is not defined for every strat ... | results/pre06_sampling_frame.md | yes | (nothing) |
| E-05 | V | DERIVED | One stratum cannot be given the registered minimum insid ... | results/pre06_sampling_frame.md | yes | (nothing) |
| E-06 | V | DERIVED | Under the measured planning correlation the effective sa ... | results/pre06_sampling_frame.md | yes | (nothing) |
| E-07 | V | MEASURED | No draw and no fetch has occurred. The frame is fenced i ... | colophon/sample.py | yes | (nothing) |
| F2-01 | F2 | MEASURED | The writer census recomputed from what the census read o ... | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | yes | (nothing) |
| F2-02 | F2 | MEASURED | Opening the files attributes a writer to the large major ... | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | yes | (nothing) |
| F2-03 | F2 | MEASURED | Where both carriers name a toolkit, they disagree about ... | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | yes | (nothing) |
| F2-04 | F2 | MEASURED | One file-meta implementation identity carries several di ... | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | yes | (nothing) |
| F2-05 | F2 | MEASURED | The Phase 1 floor set, presented per writer, per validat ... | results/manuscript/table2_floor_set.csv and results/manuscript/table2_floor_set.md | yes | (nothing) |
| F2-06 | F2 | MEASURED | The SEG BINARY overlap under dicom-validator, recomputed ... | results/manuscript/table2_floor_set.csv and results/manuscript/table2_floor_set.md | yes | (nothing) |
| F2-07 | F2 | MEASURED | Part of the Phase 1 fixture floor is drawn by corpus obj ... | results/manuscript/table2_floor_set.csv and results/manuscript/table2_floor_set.md | yes | (nothing) |
| F2-08 | F2 | MEASURED | Table 1 covers only SOP classes the census has finished, ... | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | yes | (nothing) |
| F2-09 | F2 | MEASURED | The census records file was read while a census was appe ... | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | yes | (nothing) |
| F2-10 | F2 | MEASURED | The equipment-attribute rule attributes objects to QIICR ... | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | yes | (nothing) |
| F3-01 | F3 | MEASURED | Every claim in the ledger is mapped to its row and to th ... | results/claims_map.csv and results/claims_map.md | yes | (nothing) |
| F3-02 | F3 | MEASURED | Orphan claims, meaning ledger rows with no artefact behi ... | results/claims_map.csv and results/claims_map.md | yes | (nothing) |
| F3-03 | F3 | MEASURED | Uncited artefacts, meaning files under results/ that no ... | results/claims_map.csv and results/claims_map.md | yes | (nothing) |
| F3-04 | F3 | MEASURED | Every derived_from reference in the ledger resolves to a ... | results/claims_map.csv and results/claims_map.md | yes | (nothing) |
| F3-05 | F3 | MEASURED | Every retired claim keeps its reason, and the chain from ... | results/claims_map.csv and results/claims_map.md | yes | (nothing) |
| F3-06 | F3 | MEASURED | Pre-registration rows and whether an outcome has been re ... | results/claims_map.csv and results/claims_map.md | yes | (nothing) |
| F3-07 | F3 | MEASURED | Floor coverage: which MEASURED rows quote a rate, and wh ... | results/claims_map.csv and results/claims_map.md | yes | (nothing) |
| F3-08 | F3 | MEASURED | Test coverage of the ledger: which rows name a pinning t ... | results/claims_map.csv and results/claims_map.md | yes | (nothing) |
| G1-01 | G1 | LITERATURE | A recheck on 2026-08-02 located nothing published on or ... | results/prior_art_recheck.md | yes | (nothing) |
| G1-02 | G1 | LITERATURE | No prior description was located of Key Object Selection ... | results/prior_art_recheck.md | yes | (nothing) |
| G1-03 | G1 | VERIFIED | The General Equipment module is Mandatory in the Key Obj ... | results/prior_art_recheck.md | yes | (nothing) |
| G1-04 | G1 | LITERATURE | The dciodvfy check that fires on Referenced Frame Number ... | results/prior_art_recheck.md | yes | (nothing) |
| G1-05 | G1 | LITERATURE | The underlying encoding defect behind finding (b), Refer ... | results/prior_art_recheck.md | yes | (nothing) |
| G1-06 | G1 | PENDING | dciodvfy emits two different wordings for the same Refer ... | results/prior_art_recheck.md | yes | (nothing) |
| G1-07 | G1 | LITERATURE | Finding (c), Laterality (0020,0060) reported as an Error ... | results/prior_art_recheck.md | yes | (nothing) |
| G1-08 | G1 | LITERATURE | The dciodvfy author frames the Laterality behaviour as d ... | results/prior_art_recheck.md | yes | (nothing) |
| G1-09 | G1 | PENDING | Three source classes that could falsify a novelty claim ... | results/prior_art_recheck.md | yes | (nothing) |
| G1-10 | G1 | PENDING | The prior art recheck must be re-run at a useful interva ... | results/prior_art_recheck.md | yes | (nothing) |
| G2-01 | G2 | MEASURED | The prior-art search is reported against the 16 PRISMA-S ... | results/prisma_s_appendix.md and results/prisma_s_rows.csv | yes | (nothing) |
| G2-02 | G2 | MEASURED | Most recorded queries carry no hit count, so their count ... | results/prisma_s_appendix.md and results/prisma_s_rows.csv | yes | (nothing) |
| G2-03 | G2 | MEASURED | Stated as a rule: a negative prior-art claim is auditabl ... | results/prisma_s_appendix.md and results/prisma_s_rows.csv | yes | (nothing) |
| G2-04 | G2 | MEASURED | Hit counts from general web search are not reproducible ... | results/prisma_s_appendix.md and results/prisma_s_rows.csv | yes | (nothing) |
| G2-05 | G2 | MEASURED | The existing search record cannot fill a defined set of ... | results/prisma_s_appendix.md and results/prisma_s_rows.csv | yes | (nothing) |
| G2-06 | G2 | MEASURED | Most included records have no entry in the recorded retr ... | results/prisma_s_appendix.md and results/prisma_s_rows.csv | yes | (nothing) |
| G2-07 | G2 | MEASURED | No repository, issue tracker or documentation site was s ... | results/prisma_s_appendix.md and results/prisma_s_rows.csv | yes | (nothing) |
| G3-01 | G3 | VERIFIED | The IHE AIR Rev 1.3 PDF at the pinned URL is byte identi ... | results/ihe_air_table.md | yes | (nothing) |
| G3-02 | G3 | VERIFIED | Table 6.5.3.1-1 on printed page 82 has four columns and ... | results/ihe_air_table.md | yes | (nothing) |
| G3-03 | G3 | VERIFIED | Table 6.5.3.1-1 imposes no requirement of its own. It is ... | results/ihe_air_table.md | yes | (nothing) |
| G3-04 | G3 | DERIVED | Table 6.5.3.1-1 adds no requirement beyond the unconditi ... | results/ihe_air_table.md | yes | (nothing) |
| G3-05 | G3 | VERIFIED | The four column grid of Table 6.5.3.1-1, previously reco ... | results/ihe_air_table.md | yes | (nothing) |
| F1-M-01 | F1M | MEASURED | A Methods section for the Journal of Imaging Informatics ... | results/manuscript/methods.md | yes | (nothing) |
| F1-M-02 | F1M | DERIVED | The Methods draft consumes and cites by id the ledger ro ... | results/manuscript/methods.md | yes | (nothing) |
| F1-M-03 | F1M | PENDING | Three figures the Methods section would use for reproduc ... | results/manuscript/methods.md | yes | (nothing) |
| F1-M-04 | F1M | PENDING | Ledger row V-09 states in its claim text that four tools ... | results/panel.json | yes | (nothing) |
| F4-01 | F4M | MEASURED | Census completeness was recounted directly from the cens ... | results/manuscript/results.md | yes | (nothing) |
| F4-02 | F4M | MEASURED | Comprehensive 3D SR Storage is complete in the census an ... | results/manuscript/results.md | yes | (nothing) |
| F4-03 | F4M | MEASURED | A Results section is drafted at results/manuscript/resul ... | results/manuscript/results.md | yes | (nothing) |
| F4-04 | F4M | DERIVED | The Results draft consumes and cites by id the ledger ro ... | results/manuscript/results.md | yes | (nothing) |
| F4-05 | F4M | MEASURED | The rule that a partial class must not be reported with ... | tests/test_results_doc.py | yes | (nothing) |
| C-C3D-01 | C-C3D | VERIFIED | Clinical Trial Site Name (0012,0031) and Clinical Trial ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| C-C3D-02 | C-C3D | VERIFIED | De-identification Method (0012,0063) and De-identificati ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| C-C3D-03 | C-C3D | VERIFIED | A Referenced Study Sequence Item without Referenced SOP ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| C-C3D-04 | C-C3D | VERIFIED | Ethnic Group (0010,2160) present in a 2026c object is a ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | (nothing) |
| C-C3D-05 | C-C3D | VERIFIED | Procedure Code Sequence (0008,1032) present with zero It ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | (nothing) |
| C-C3D-06 | C-C3D | MEASURED | dciodvfy error triple for Comprehensive 3D SR Storage, a ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md |
| C-C3D-07 | C-C3D | MEASURED | dciodvfy warning triple for Comprehensive 3D SR Storage, ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | (nothing) |
| C-C3D-08 | C-C3D | MEASURED | dicom-validator error triple for Comprehensive 3D SR Sto ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md |
| C-C3D-09 | C-C3D | MEASURED | Net rate across both validators for Comprehensive 3D SR ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| C-C3D-10 | C-C3D | MEASURED | Collection-level net rates for Comprehensive 3D SR Stora ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| C-C3D-11 | C-C3D | MEASURED | Two adjudications in this class are reported both ways, ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | (nothing) |
| C-C3D-12 | C-C3D | DERIVED | PRE-05 outcome for Comprehensive 3D SR Storage, and the ... | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | yes | results/manuscript/results.md; results/phase2/net_rates_comprehensive_3d_sr.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| P3-01 | P3 | MEASURED | Among sampled Segmentation segments declaring SegmentAlg ... | results/phase3/seg_identification_segments_by_stratum.csv | yes | results/cp/README.md; results/figures/manifest.json; results/manuscript/figures.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/05_figure_legends.md; results/typecheck/type_reverification.csv |
| P3-02 | P3 | MEASURED | Among the same segments, this fraction carries Segmentat ... | results/phase3/seg_missing_type1_children.csv | yes | results/cp/README.md; results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/typecheck/type_reverification.csv |
| P3-03 | P3 | MEASURED | A third state exists and is reported separately from bot ... | results/phase3/seg_identification_segments_by_stratum.csv | yes | (nothing) |
| P3-04 | P3 | MEASURED | The object-level reading of the same question, reported ... | results/phase3/seg_identification_objects_by_stratum.csv | yes | (nothing) |
| P3-05 | P3 | MEASURED | SegmentAlgorithmName (0062,0009) is Type 1C, required wh ... | results/phase3/seg_identification_segments_by_stratum.csv | yes | results/cp/README.md; results/figures/manifest.json; results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/figures.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/05_figure_legends.md; results/typecheck/type_reverification.csv |
| P3-06 | P3 | MEASURED | The full provenance carrier list on sampled Segmentation ... | results/phase3/seg_carriers_by_stratum.csv | yes | results/typecheck/type_reverification.csv |
| P3-07 | P3 | MEASURED | dciodvfy and dicom-validator message classes over the sa ... | results/phase3/seg_message_classes.csv | yes | (nothing) |
| P3-08 | P3 | DERIVED | The population estimate for the absence and incompletene ... | results/phase3/seg_totals.json | yes | (nothing) |
| P3-12 | P3 | MEASURED | The frame's writer label is provisional and the object c ... | results/phase3/seg_writer_relabel.csv | yes | results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| P3-11 | P3 | MEASURED | SegmentAlgorithmType (0062,0008) is Type 1 with Enumerat ... | results/phase3/seg_out_of_enumeration.csv | yes | results/typecheck/type_reverification.csv |
| P3-10 | P3 | MEASURED | A complete Algorithm Identification Macro is not the sam ... | results/phase3/seg_macro_content.csv | yes | results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| P3-09 | P3 | MEASURED | Two of the three conformance tools in this class's panel ... | results/phase3_segmentation.md | yes | results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| C3T-00 | C3T | MEASURED | Claim 3 is graded in three ways and never two: non-confo ... | results/claim3/grades_by_sop_class.csv | yes | results/figures/manifest.json; results/manuscript/figures.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md |
| C3T-01 | C3T | MEASURED | T3.1. Carrier population across the tabulation, in three ... | results/claim3/t31_carriers_by_sop_class.csv | yes | results/manuscript/tables.md; results/submission/04_tables.md |
| C3T-08 | C3T | MEASURED | Type 1 carrier violations found by the three-state captu ... | results/claim3/t31_type1_validator_corroboration.csv | yes | results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/typecheck/type_reverification.csv |
| C3T-02 | C3T | MEASURED | T3.2. What the equipment attributes name, not whether th ... | results/claim3/t32_naming_by_sop_class.csv | yes | results/figures/manifest.json; results/manuscript/discussion.md; results/manuscript/figures.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/05_figure_legends.md |
| C3T-03 | C3T | MEASURED | T3.3. The recoverability ladder. Per analysis result, th ... | results/claim3/t33_recoverability_ladder.csv | yes | results/figures/manifest.json; results/manuscript/figures.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md |
| C3T-04 | C3T | MEASURED | T3.4. The algorithm identification result stratified by ... | results/claim3/t34_algorithm_identification_by_writer.csv | yes | (nothing) |
| C3T-05 | C3T | MEASURED | T3.4 special row. Segments carrying a complete and confo ... | results/claim3/t34_complete_macro_naming_manual.csv | yes | results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| C3T-06 | C3T | MEASURED | T3.5. Version carriers. The dcmqi SoftwareVersions value ... | results/claim3/t35_version_carriers.csv | yes | results/figures/manifest.json; results/manuscript/figures.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md; results/typecheck/type_reverification.csv |
| C3T-07 | C3T | MEASURED | T3.6. The archive catalogue and the object disagree abou ... | results/claim3/t36_writer_index_vs_object_by_sop_class.csv | yes | results/manuscript/discussion.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| ADJ2-01 | ADJ2 | MEASURED | PRE-03 registers two adjudicators. A second pass was run ... | ADJUDICATION2.md | yes | results/figures/manifest.json; results/manuscript/figures.md; results/manuscript/methods.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md |
| ADJ2-02 | ADJ2 | MEASURED | The only adjudication decision that reaches a published ... | ADJUDICATION2.md | yes | results/figures/manifest.json; results/manuscript/figures.md; results/manuscript/methods.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md |
| ADJ2-03 | ADJ2 | MEASURED | Net rates recomputed under the consensus rule, where a c ... | results/adjudication2/net_rates_two_pass.csv | yes | results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md |
| DEV-01 | DEV | MEASURED | The dicom3tools pin registered for this study was never ... | DEVIATIONS.md | yes | results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/methods.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| DEV-02 | DEV | MEASURED | The highdicom pin registered for this study was never sa ... | DEVIATIONS.md | yes | results/figures/manifest.json; results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/figures.md; results/manuscript/methods.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md |
| C3T-09 | C3T | MEASURED | The informativeness grade is sensitive to the rule that ... | results/claim3/grades_by_sop_class.csv and results/ai_use.md | yes | results/manuscript/methods.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| STD-07 | STD | VERIFIED | Every Type designation the manuscript relies on reproduc ... | TYPECHECK.md and results/typecheck/type_reverification.csv | yes | results/cp/README.md; results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/methods.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| STD-08 | STD | VERIFIED | The provenance ceiling has three tiers, not one. General ... | results/typecheck/equipment_module_usage_by_iod.csv | yes | results/figures/manifest.json; results/manuscript/figures.md; results/manuscript/methods.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md; results/submission/05_figure_legends.md |
| V-11 | V | VERIFIED | The dciodvfy person-name check is purely syntactic and c ... | COLOPHON_ADDENDUM_03.md and results/manuscript/methods.md | yes | (nothing) |
| PA-10 | PA | MEASURED | Two of the three DICOM attribute names this study measur ... | results/prisma_s_rows.csv | yes | results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/manuscript/introduction.md; results/prisma_s_rows.csv; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| PA-11 | PA | MEASURED | No DICOM Correction Proposal in the complete numbered se ... | results/prisma_s_rows.csv | yes | results/cp/README.md; results/manuscript/discussion.md; results/prisma_s_rows.csv; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| STD-09 | STD | VERIFIED | Table C.8.20-4, the Segment Description Macro, carries S ... | results/typecheck/segment_tables_verbatim.md | yes | (nothing) |
| STD-10 | STD | VERIFIED | Supplement 243, Label Map Segmentation, Final Text 2024, ... | results/typecheck/segment_tables_verbatim.md | yes | results/cp/README.md; results/manuscript/discussion.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md |
| C3T-10 | C3T | MEASURED | The object-weighted headline is concentrated in one clas ... | results/manuscript/table2.csv | yes | (nothing) |
| FIG-01 | FIG | MEASURED | Six figures are drawn, each from a single named artefact ... | results/manuscript/figures.md and results/figures/manifest.json | yes | (nothing) |
| REF-01 | REF | MEASURED | Every citation in the manuscript resolves to a full refe ... | results/manuscript/references.md and results/manuscript/citation_check.json | yes | (nothing) |
| REF-02 | REF | VERIFIED | The Gene Expression Omnibus metadata completeness study ... | results/manuscript/references.md | yes | results/ai_use.md; results/manuscript/references.md |
| REF-03 | REF | VERIFIED | The software bill-of-materials study cited in the Discus ... | results/manuscript/references.md | yes | results/manuscript/references.md |
| REF-04 | REF | VERIFIED | The IHE AIR passage quoted verbatim in the Discussion is ... | results/manuscript/citation_check.json | yes | (nothing) |
| REF-05 | REF | VERIFIED | CP-2273 is in the standard at edition 2026b. The status ... | results/cp/dicom_status_rows.json | yes | results/ai_use.md |
| REF-06 | REF | VERIFIED | The five other Correction Proposals and Supplement 243 c ... | results/cp/dicom_status_rows.json | yes | (nothing) |
| FM-01 | FM | VERIFIED | The author identifiers in the front matter are read from ... | results/manuscript/front_matter.md | yes | (nothing) |
| FM-02 | FM | PENDING | No Zenodo record exists for this repository, so code ava ... | results/manuscript/front_matter.md | yes | results/submission/07_checklist.md |
| FM-03 | FM | VERIFIED | The commercial relationship disclosed in competing inter ... | results/manuscript/front_matter.md | yes | (nothing) |
| CPD-01 | CPD | PENDING | A DICOM Correction Proposal harmonising the Type of Segm ... | results/cp/cp_segmentation_algorithm_identification.md and results/cp/README.md | yes | results/cp/EMAIL.md |
| CPD-02 | CPD | VERIFIED | The wording the proposal asks for already exists in the ... | results/typecheck/segment_tables_verbatim.md and results/typecheck/type_reverification.csv | yes | results/ai_use.md |
| CPD-03 | CPD | DERIVED | Adopting the proposed change would make previously confo ... | results/cp/cp_segmentation_algorithm_identification.md | yes | results/ai_use.md |
| FIG-02 | FIG | MEASURED | A truer exemplar for Figure 3's silent column exists: fo ... | results/figures/silent_column_check.json and results/figures/silent_column_candidates.csv and results/figures/figure3_objects.json | yes | results/ai_use.md; results/figures/manifest.json; results/manuscript/figures.md; results/submission/05_figure_legends.md |
| FIG-03 | FIG | DERIVED | Two analysis results are recorded in the recoverability ... | results/figures/silent_column_check.json | yes | results/ai_use.md; results/manuscript/results.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/assertions.json; results/submission/assertions.md |
| REF-07 | REF | VERIFIED | The reference list is generated from structured entries ... | results/manuscript/references.md and results/manuscript/references_crossref.json | yes | (nothing) |
| SUB-01 | SUB | MEASURED | The submission package is assembled from the manuscript ... | results/submission/07_checklist.md and results/submission/manifest.json | yes | (nothing) |
| SUB-02 | SUB | VERIFIED | The venue requirements the package is built against were ... | results/submission/07_checklist.md and results/submission/venue_guidelines_read_2026-08-03.txt | yes | results/ai_use.md; results/submission/venue_guidelines_read_2026-08-03.txt |
| SUB-03 | SUB | MEASURED | The abstract submitted is a 249 word form, and what the ... | results/manuscript/abstract_venue.md | yes | results/ai_use.md |
| SUB-04 | SUB | VERIFIED | The blinded copy carries no author name, affiliation, id ... | results/submission/03_manuscript_blinded.md | yes | (nothing) |
| SUB-05 | SUB | MEASURED | The venue requires a link to the imaging data used, and ... | results/submission/supplementary/S1_source_dois.csv | yes | (nothing) |
| FIG-04 | FIG | MEASURED | No figure draws a title or a caption into the illustrati ... | results/figures/manifest.json and results/manuscript/figures.md | yes | results/ai_use.md |
| FIG-05 | FIG | MEASURED | Every text colour used in the figures clears the contras ... | results/figures/manifest.json | yes | results/ai_use.md |
| FIG-06 | FIG | MEASURED | No figure is drawn wider than the venue's text column, s ... | results/submission/manifest.json | yes | results/ai_use.md |
| C3T-11 | C3T | MEASURED | The version column of the recoverability ladder carries ... | results/claim3/t33_recoverability_ladder.csv and results/manuscript/table3.csv | yes | results/ai_use.md |
| DEV-03 | DEV | MEASURED | What the caller writes into SoftwareVersions on highdico ... | results/deviations/pin_deviations.json | yes | results/ai_use.md |
| FIG-07 | FIG | DERIVED | The rule-ordering undercount recorded at FIG-03 is discl ... | results/manuscript/results.md and results/figures/silent_column_check.json | yes | results/ai_use.md |
| SUB-06 | SUB | DERIVED | The assembled manuscript body is long for an Original Pa ... | results/submission/07_checklist.md and results/submission/manifest.json | yes | (nothing) |
| SUB-07 | SUB | MEASURED | The figure set regenerates byte-identical in every forma ... | results/figures/reproducibility.json | yes | (nothing) |
| SUB-08 | SUB | MEASURED | Every row of the checklist's computed table reports some ... | results/submission/07_checklist.md | yes | (nothing) |
| DISC-01 | DISC | MEASURED | No object in the measured set is written by the disclose ... | results/claim3/disclosure_search.json | yes | results/manuscript/absence_claims.csv; results/manuscript/absence_claims.md; results/submission/00_cover_letter.md; results/submission/01_title_page.md; results/submission/02_manuscript_full.md |
| DISC-02 | DISC | MEASURED | Absence and universal claims across the package were swe ... | results/manuscript/absence_claims.md and results/manuscript/absence_claims.csv | yes | (nothing) |
| SUB-09 | SUB | MEASURED | Every placeholder in the package is a key in one JSON fi ... | results/submission/fields.json | yes | (nothing) |
| SUB-10 | SUB | MEASURED | The archived snapshot contains the code and the generate ... | results/release/snapshot.json and results/release/RELEASE_NOTES.md | yes | (nothing) |
| CPD-04 | CPD | PENDING | The Correction Proposal will be filed before submission, ... | results/cp/status.json | yes | results/cp/EMAIL.md |
| C3T-12 | C3T | MEASURED | The `(null)` cell is a residual bucket, defined where th ... | results/claim3/t33_recoverability_ladder.csv and results/manuscript/tables.md | yes | results/manuscript/methods.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md |
| C3T-13 | C3T | MEASURED | Analysis-result cells are complete for the seven censuse ... | results/manuscript/tables.md | yes | results/manuscript/methods.md; results/manuscript/results.md; results/manuscript/tables.md; results/submission/02_manuscript_full.md; results/submission/03_manuscript_blinded.md; results/submission/04_tables.md |
| SUB-11 | SUB | MEASURED | Six defects of one shape were closed by strengthening th ... | results/submission/assertions.json and results/submission/assertions.md | yes | (nothing) |
| SUB-12 | SUB | MEASURED | The six figures are renumbered so that first citation in ... | results/submission/02_manuscript_full.md and results/manuscript/figures.md | yes | (nothing) |
| SUB-13 | SUB | MEASURED | The Word files are produced from a converter pinned in i ... | results/submission/docx.json | yes | (nothing) |
| SUB-14 | SUB | VERIFIED | The competing-interests employment window is stated by t ... | results/submission/fields.json and results/submission/01_title_page.md | yes | (nothing) |
| REL-04 | REL | MEASURED | Every version string in the package derives from one sou ... | colophon/__init__.py and results/submission/02_manuscript_full.md | yes | (nothing) |
| SUB-15 | SUB | MEASURED | No identifier of any shape reaches the blinded copy, che ... | results/submission/03_manuscript_blinded.md | yes | (nothing) |

## 1. Orphan claims

A claim nothing carries is a claim that will not survive review. Two failures,
counted apart because they are not equally bad.

**No artefact behind the row: 13 of 297.** The row names no source file, or names
one that is not on disk.

| id | status | why |
|---|---|---|
| P0-12 | PENDING | names no source file |
| C3-14 | PENDING | names no source file; no results markdown names the id |
| C3-06-air | RETIRED | names no source file; no results markdown names the id |
| C3-02-prev | RETIRED | names no source file; no results markdown names the id |
| C-PM-01 | MEASURED | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-02 | VERIFIED | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-03 | VERIFIED | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-04 | VERIFIED | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-05 | MEASURED | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-06 | MEASURED | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-07 | MEASURED | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-08 | MEASURED | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-09 | DERIVED | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md |

**No results markdown names the id: 196 of 297.** The evidence file exists, but no
write-up refers to the claim by id, so the route from prose to ledger row is one
a reader has to reconstruct.

Under the union of the two conditions, **198 of 297 rows are orphans**.

| id | status | source_file | why |
|---|---|---|---|
| P0-01 | MEASURED | results/phase0/census_all.csv | no results markdown names the id |
| P0-02 | MEASURED | results/phase0/census_derived.csv | no results markdown names the id |
| P0-03 | MEASURED | results/phase0/census_derived.csv | no results markdown names the id |
| P0-06 | MEASURED | results/phase0/parametric_map.csv | no results markdown names the id |
| P0-07 | MEASURED | results/phase0/licenses.csv | no results markdown names the id |
| P0-08 | MEASURED | results/phase0/phase2_budget.csv | no results markdown names the id |
| P0-09 | MEASURED | results/phase0_census.md and results/phase0/*.csv | no results markdown names the id |
| P0-12 | PENDING | (none) | names no source file |
| P0-10 | MEASURED | results/phase0/census_by_analysis_result.csv | no results markdown names the id |
| C3-01 | MEASURED | results/phase0/provenance_population_by_sop.csv | no results markdown names the id |
| C3-02 | MEASURED | results/phase0/provenance_buckets.csv | no results markdown names the id |
| C3-03 | MEASURED | results/phase0/provenance_converter_pairs.csv | no results markdown names the id |
| C3-10 | MEASURED | results/phase0/provenance_conventions.csv | no results markdown names the id |
| C3-04 | MEASURED | results/phase0/provenance_spelling_variants.csv | no results markdown names the id |
| C3-05 | MEASURED | results/phase0/provenance_name_agreement.csv | no results markdown names the id |
| C3-06 | PENDING | results/claim3_provenance.md and results/phase0/provenance_*.csv | no results markdown names the id |
| C3-07 | MEASURED | results/phase0/provenance_acquisition_inheritance.csv | no results markdown names the id |
| C3-08 | MEASURED | results/claim3_provenance.md and results/phase0/provenance_*.csv | no results markdown names the id |
| C3-14 | PENDING | (none) | names no source file; no results markdown names the id |
| C3-06-air | RETIRED | (none) | names no source file; no results markdown names the id |
| C3-15 | MEASURED | results/sentinels.json | no results markdown names the id |
| C3-02-prev | RETIRED | (none) | names no source file; no results markdown names the id |
| C3-09 | PENDING | results/claim3_provenance.md and results/phase0/provenance_*.csv | no results markdown names the id |
| PA-02 | LITERATURE | results/prior_art.md | no results markdown names the id |
| PA-03-prev | RETIRED | results/prior_art.md | no results markdown names the id |
| PA-04 | LITERATURE | results/prior_art.md | no results markdown names the id |
| W-02 | MEASURED | results/phase0/carrier_hierarchy.csv | no results markdown names the id |
| W-03 | MEASURED | results/phase0/cohort_recall.json | no results markdown names the id |
| W-04 | MEASURED | results/sentinels.json | no results markdown names the id |
| V-01 | MEASURED | results/panel.json | no results markdown names the id |
| V-02 | MEASURED | results/panel.json | no results markdown names the id |
| V-03 | MEASURED | results/panel.json | no results markdown names the id |
| V-07 | MEASURED | results/panel.json | no results markdown names the id |
| V-08 | MEASURED | results/panel.json | no results markdown names the id |
| V-09 | MEASURED | results/panel.json | no results markdown names the id |
| V-10 | PENDING | results/panel.json | no results markdown names the id |
| STD-01 | VERIFIED | results/standards.json | no results markdown names the id |
| STD-02-hyp | RETIRED | results/standards.json | no results markdown names the id |
| STD-05 | MEASURED | results/standards.json | no results markdown names the id |
| STD-06-untested | RETIRED | results/standards.json | no results markdown names the id |
| F1-02 | MEASURED | results/floor_set.csv | no results markdown names the id |
| F1-04 | MEASURED | results/floor_set.csv | no results markdown names the id |
| F1-06 | MEASURED | results/floor_set.csv | no results markdown names the id |
| F1-07 | MEASURED | results/floor_set.csv | no results markdown names the id |
| F1-08 | PENDING | results/floor_set.csv | no results markdown names the id |
| F1-09 | MEASURED | results/floor_set.csv | no results markdown names the id |
| P2P-01 | MEASURED | results/phase2/pilot_provenance.csv | no results markdown names the id |
| P2P-02 | MEASURED | results/phase2/pilot_message_classes.csv | no results markdown names the id |
| P2P-03 | MEASURED | results/phase2/pilot_message_classes.csv | no results markdown names the id |
| P2P-04 | MEASURED | results/phase2/pilot_provenance.csv | no results markdown names the id |
| P2P-06 | MEASURED | results/phase2/pilot_provenance.csv | no results markdown names the id |
| P2P-07 | MEASURED | results/phase2/pilot_fetch_log.csv | no results markdown names the id |
| P2C-03 | MEASURED | results/phase2/census_provenance_states.csv | no results markdown names the id |
| B-01 | MEASURED | results/phase1_variants.csv | no results markdown names the id |
| B-04 | MEASURED | results/phase1_variants.csv | no results markdown names the id |
| B-06 | MEASURED | results/phase1_variants.csv | no results markdown names the id |
| B-07 | MEASURED | results/phase1_variants.csv | no results markdown names the id |
| B-08 | MEASURED | results/phase1_variants.csv | no results markdown names the id |
| B-09 | MEASURED | results/phase1_variants.csv | no results markdown names the id |
| B-11 | PENDING | results/phase1_variants.csv | no results markdown names the id |
| C-CSR-01 | VERIFIED | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | no results markdown names the id |
| C-CSR-02 | VERIFIED | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | no results markdown names the id |
| C-CSR-03 | VERIFIED | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | no results markdown names the id |
| C-CSR-04 | VERIFIED | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | no results markdown names the id |
| C-CSR-05 | MEASURED | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | no results markdown names the id |
| C-CSR-06 | MEASURED | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | no results markdown names the id |
| C-CSR-07 | MEASURED | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | no results markdown names the id |
| C-CSR-08 | MEASURED | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | no results markdown names the id |
| C-CSR-09 | MEASURED | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | no results markdown names the id |
| C-CSR-10 | MEASURED | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | no results markdown names the id |
| C-CSR-11 | DERIVED | results/phase2/adjudication_comprehensive_sr.csv and results/phase2/net_rates_comprehensive_sr.md | no results markdown names the id |
| C-GSPS-01 | MEASURED | results/phase2/net_rates_gsps.md | no results markdown names the id |
| C-GSPS-02 | MEASURED | results/phase2/net_rates_gsps.md | no results markdown names the id |
| C-GSPS-03 | MEASURED | results/phase2/net_rates_gsps.md | no results markdown names the id |
| C-GSPS-04 | VERIFIED | results/phase2/adjudication_gsps.csv | no results markdown names the id |
| C-GSPS-05 | VERIFIED | results/phase2/adjudication_gsps.csv | no results markdown names the id |
| C-GSPS-06 | VERIFIED | results/phase2/adjudication_gsps.csv | no results markdown names the id |
| C-GSPS-07 | VERIFIED | results/phase2/net_rates_gsps.md | no results markdown names the id |
| C-GSPS-08 | MEASURED | results/phase2/net_rates_gsps.md | no results markdown names the id |
| C-GSPS-09 | DERIVED | results/phase2/net_rates_gsps.md | no results markdown names the id |
| C-GSPS-10 | DERIVED | results/phase2/net_rates_gsps.md | no results markdown names the id |
| C-GSPS-11 | VERIFIED | results/phase2/adjudication_gsps.csv | no results markdown names the id |
| C-PM-01 | MEASURED | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-02 | VERIFIED | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-03 | VERIFIED | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-04 | VERIFIED | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-05 | MEASURED | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-06 | MEASURED | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-07 | MEASURED | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-08 | MEASURED | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md; no results markdown names the id |
| C-PM-09 | DERIVED | results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md | source file missing: results/phase2/adjudication_parametric_map.csv; results/phase2/net_rates_parametric_map.md |
| C-RWV-01 | MEASURED | results/phase2/net_rates_rwv_kos.md | no results markdown names the id |
| C-RWV-02 | MEASURED | results/phase2/net_rates_rwv_kos.md | no results markdown names the id |
| C-RWV-03 | MEASURED | results/phase2/net_rates_rwv_kos.md | no results markdown names the id |
| C-RWV-04 | VERIFIED | results/phase2/adjudication_rwv_kos.csv | no results markdown names the id |
| C-RWV-05 | VERIFIED | results/phase2/adjudication_rwv_kos.csv | no results markdown names the id |
| C-RWV-06 | VERIFIED | results/phase2/adjudication_rwv_kos.csv | no results markdown names the id |
| C-RWV-07 | VERIFIED | results/phase2/adjudication_rwv_kos.csv | no results markdown names the id |
| C-KOS-01 | MEASURED | results/phase2/net_rates_rwv_kos.md | no results markdown names the id |
| C-KOS-02 | MEASURED | results/phase2/net_rates_rwv_kos.md | no results markdown names the id |
| C-KOS-03 | MEASURED | results/phase2/net_rates_rwv_kos.md | no results markdown names the id |
| C-KOS-04 | VERIFIED | results/phase2/adjudication_rwv_kos.csv | no results markdown names the id |
| C-RWV-08 | DERIVED | results/phase2/net_rates_rwv_kos.md | no results markdown names the id |
| C-KOS-05 | DERIVED | results/phase2/net_rates_rwv_kos.md | no results markdown names the id |
| D-02 | MEASURED | results/phase2/census_message_classes.csv | no results markdown names the id |
| D-03 | MEASURED | results/phase2/gsps_dcmpschk.csv | no results markdown names the id |
| E-01 | MEASURED | results/phase0/seg_strata.csv | no results markdown names the id |
| E-02 | DERIVED | results/pre06_sampling_frame.md | no results markdown names the id |
| E-03 | MEASURED | results/phase0/seg_icc_proxies.csv | no results markdown names the id |
| E-04 | DERIVED | results/pre06_sampling_frame.md | no results markdown names the id |
| E-05 | DERIVED | results/pre06_sampling_frame.md | no results markdown names the id |
| E-06 | DERIVED | results/pre06_sampling_frame.md | no results markdown names the id |
| E-07 | MEASURED | colophon/sample.py | no results markdown names the id |
| F2-01 | MEASURED | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | no results markdown names the id |
| F2-02 | MEASURED | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | no results markdown names the id |
| F2-03 | MEASURED | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | no results markdown names the id |
| F2-04 | MEASURED | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | no results markdown names the id |
| F2-05 | MEASURED | results/manuscript/table2_floor_set.csv and results/manuscript/table2_floor_set.md | no results markdown names the id |
| F2-06 | MEASURED | results/manuscript/table2_floor_set.csv and results/manuscript/table2_floor_set.md | no results markdown names the id |
| F2-07 | MEASURED | results/manuscript/table2_floor_set.csv and results/manuscript/table2_floor_set.md | no results markdown names the id |
| F2-08 | MEASURED | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | no results markdown names the id |
| F2-09 | MEASURED | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | no results markdown names the id |
| F2-10 | MEASURED | results/manuscript/table1_writers.csv and results/manuscript/table1_writers.md | no results markdown names the id |
| F3-01 | MEASURED | results/claims_map.csv and results/claims_map.md | no results markdown names the id |
| F3-02 | MEASURED | results/claims_map.csv and results/claims_map.md | no results markdown names the id |
| F3-03 | MEASURED | results/claims_map.csv and results/claims_map.md | no results markdown names the id |
| F3-04 | MEASURED | results/claims_map.csv and results/claims_map.md | no results markdown names the id |
| F3-05 | MEASURED | results/claims_map.csv and results/claims_map.md | no results markdown names the id |
| F3-06 | MEASURED | results/claims_map.csv and results/claims_map.md | no results markdown names the id |
| F3-07 | MEASURED | results/claims_map.csv and results/claims_map.md | no results markdown names the id |
| F3-08 | MEASURED | results/claims_map.csv and results/claims_map.md | no results markdown names the id |
| G1-01 | LITERATURE | results/prior_art_recheck.md | no results markdown names the id |
| G1-02 | LITERATURE | results/prior_art_recheck.md | no results markdown names the id |
| G1-03 | VERIFIED | results/prior_art_recheck.md | no results markdown names the id |
| G1-04 | LITERATURE | results/prior_art_recheck.md | no results markdown names the id |
| G1-05 | LITERATURE | results/prior_art_recheck.md | no results markdown names the id |
| G1-06 | PENDING | results/prior_art_recheck.md | no results markdown names the id |
| G1-07 | LITERATURE | results/prior_art_recheck.md | no results markdown names the id |
| G1-08 | LITERATURE | results/prior_art_recheck.md | no results markdown names the id |
| G1-09 | PENDING | results/prior_art_recheck.md | no results markdown names the id |
| G1-10 | PENDING | results/prior_art_recheck.md | no results markdown names the id |
| G2-01 | MEASURED | results/prisma_s_appendix.md and results/prisma_s_rows.csv | no results markdown names the id |
| G2-02 | MEASURED | results/prisma_s_appendix.md and results/prisma_s_rows.csv | no results markdown names the id |
| G2-03 | MEASURED | results/prisma_s_appendix.md and results/prisma_s_rows.csv | no results markdown names the id |
| G2-04 | MEASURED | results/prisma_s_appendix.md and results/prisma_s_rows.csv | no results markdown names the id |
| G2-05 | MEASURED | results/prisma_s_appendix.md and results/prisma_s_rows.csv | no results markdown names the id |
| G2-06 | MEASURED | results/prisma_s_appendix.md and results/prisma_s_rows.csv | no results markdown names the id |
| G2-07 | MEASURED | results/prisma_s_appendix.md and results/prisma_s_rows.csv | no results markdown names the id |
| G3-01 | VERIFIED | results/ihe_air_table.md | no results markdown names the id |
| G3-02 | VERIFIED | results/ihe_air_table.md | no results markdown names the id |
| G3-03 | VERIFIED | results/ihe_air_table.md | no results markdown names the id |
| G3-04 | DERIVED | results/ihe_air_table.md | no results markdown names the id |
| G3-05 | VERIFIED | results/ihe_air_table.md | no results markdown names the id |
| F1-M-01 | MEASURED | results/manuscript/methods.md | no results markdown names the id |
| F1-M-02 | DERIVED | results/manuscript/methods.md | no results markdown names the id |
| F1-M-03 | PENDING | results/manuscript/methods.md | no results markdown names the id |
| F1-M-04 | PENDING | results/panel.json | no results markdown names the id |
| F4-01 | MEASURED | results/manuscript/results.md | no results markdown names the id |
| F4-02 | MEASURED | results/manuscript/results.md | no results markdown names the id |
| F4-03 | MEASURED | results/manuscript/results.md | no results markdown names the id |
| F4-04 | DERIVED | results/manuscript/results.md | no results markdown names the id |
| F4-05 | MEASURED | tests/test_results_doc.py | no results markdown names the id |
| C-C3D-04 | VERIFIED | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | no results markdown names the id |
| C-C3D-05 | VERIFIED | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | no results markdown names the id |
| C-C3D-07 | MEASURED | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | no results markdown names the id |
| C-C3D-11 | MEASURED | results/phase2/adjudication_comprehensive_3d_sr.csv and results/phase2/net_rates_comprehensive_3d_sr.md | no results markdown names the id |
| P3-03 | MEASURED | results/phase3/seg_identification_segments_by_stratum.csv | no results markdown names the id |
| P3-04 | MEASURED | results/phase3/seg_identification_objects_by_stratum.csv | no results markdown names the id |
| P3-06 | MEASURED | results/phase3/seg_carriers_by_stratum.csv | no results markdown names the id |
| P3-07 | MEASURED | results/phase3/seg_message_classes.csv | no results markdown names the id |
| P3-08 | DERIVED | results/phase3/seg_totals.json | no results markdown names the id |
| P3-11 | MEASURED | results/phase3/seg_out_of_enumeration.csv | no results markdown names the id |
| C3T-04 | MEASURED | results/claim3/t34_algorithm_identification_by_writer.csv | no results markdown names the id |
| V-11 | VERIFIED | COLOPHON_ADDENDUM_03.md and results/manuscript/methods.md | no results markdown names the id |
| STD-09 | VERIFIED | results/typecheck/segment_tables_verbatim.md | no results markdown names the id |
| C3T-10 | MEASURED | results/manuscript/table2.csv | no results markdown names the id |
| FIG-01 | MEASURED | results/manuscript/figures.md and results/figures/manifest.json | no results markdown names the id |
| REF-01 | MEASURED | results/manuscript/references.md and results/manuscript/citation_check.json | no results markdown names the id |
| REF-04 | VERIFIED | results/manuscript/citation_check.json | no results markdown names the id |
| REF-06 | VERIFIED | results/cp/dicom_status_rows.json | no results markdown names the id |
| FM-01 | VERIFIED | results/manuscript/front_matter.md | no results markdown names the id |
| FM-03 | VERIFIED | results/manuscript/front_matter.md | no results markdown names the id |
| REF-07 | VERIFIED | results/manuscript/references.md and results/manuscript/references_crossref.json | no results markdown names the id |
| SUB-01 | MEASURED | results/submission/07_checklist.md and results/submission/manifest.json | no results markdown names the id |
| SUB-04 | VERIFIED | results/submission/03_manuscript_blinded.md | no results markdown names the id |
| SUB-05 | MEASURED | results/submission/supplementary/S1_source_dois.csv | no results markdown names the id |
| SUB-06 | DERIVED | results/submission/07_checklist.md and results/submission/manifest.json | no results markdown names the id |
| SUB-07 | MEASURED | results/figures/reproducibility.json | no results markdown names the id |
| SUB-08 | MEASURED | results/submission/07_checklist.md | no results markdown names the id |
| DISC-02 | MEASURED | results/manuscript/absence_claims.md and results/manuscript/absence_claims.csv | no results markdown names the id |
| SUB-09 | MEASURED | results/submission/fields.json | no results markdown names the id |
| SUB-10 | MEASURED | results/release/snapshot.json and results/release/RELEASE_NOTES.md | no results markdown names the id |
| SUB-11 | MEASURED | results/submission/assertions.json and results/submission/assertions.md | no results markdown names the id |
| SUB-12 | MEASURED | results/submission/02_manuscript_full.md and results/manuscript/figures.md | no results markdown names the id |
| SUB-13 | MEASURED | results/submission/docx.json | no results markdown names the id |
| SUB-14 | VERIFIED | results/submission/fields.json and results/submission/01_title_page.md | no results markdown names the id |
| REL-04 | MEASURED | colophon/__init__.py and results/submission/02_manuscript_full.md | no results markdown names the id |
| SUB-15 | MEASURED | results/submission/03_manuscript_blinded.md | no results markdown names the id |

## 2. Uncited artefacts

Files under `results/` that no ledger row's `source_file` points at. **85 of 210
scanned files.** An artefact no claim rests on is either dead weight or an
unrecorded claim, and the two are told apart by opening the file, not by this
table. Where a parallel track has already proposed a row naming the file, the
note says so: those stop being uncited when
`python -m colophon.merge_ledger` folds the proposals in.

| file | note |
|---|---|
| results/README.md |  |
| results/adjudication2/agreement.json |  |
| results/adjudication2/two_pass_comparison.csv |  |
| results/claim3/encoder_only_by_analysis_result.csv |  |
| results/claim3/encoder_only_by_collection.csv |  |
| results/claim3/grades_by_analysis_result.csv |  |
| results/claim3/t31_carriers_by_analysis_result.csv |  |
| results/claim3/t31_type1_violations.csv |  |
| results/claim3/t32_naming_by_analysis_result.csv |  |
| results/claim3/t32_unclassified_values.csv |  |
| results/claim3/t32_value_categories.csv |  |
| results/claim3/t36_writer_index_vs_object_by_analysis_result.csv |  |
| results/claim3/two_way_rates.json |  |
| results/claim3/writer_relabelled_by_analysis_result.csv |  |
| results/claim3/writer_relabelled_by_collection.csv |  |
| results/cp/EMAIL.md |  |
| results/deviations/pin_exposure_by_analysis_result.csv |  |
| results/environment.json |  |
| results/figures/figure1.pdf |  |
| results/figures/figure1.png |  |
| results/figures/figure2.pdf |  |
| results/figures/figure2.png |  |
| results/figures/figure3.pdf |  |
| results/figures/figure3.png |  |
| results/figures/figure4.pdf |  |
| results/figures/figure4.png |  |
| results/figures/figure5.pdf |  |
| results/figures/figure5.png |  |
| results/figures/figure6.pdf |  |
| results/figures/figure6.png |  |
| results/floor_overlap.md |  |
| results/manuscript/abstract.md |  |
| results/manuscript/discussion.md |  |
| results/manuscript/introduction.md |  |
| results/manuscript/table1.csv |  |
| results/manuscript/table4.csv |  |
| results/manuscript/table5.csv |  |
| results/manuscript/table6.csv |  |
| results/phase1_variants.md |  |
| results/phase2/adjudication_parametric_map.csv |  |
| results/phase2/pilot_messages.csv |  |
| results/phase2_census.md |  |
| results/phase2_gsps_dcmpschk.md |  |
| results/phase2_pilot.md |  |
| results/phase3/seg_algorithm_type_distribution.csv |  |
| results/phase3/seg_contributing_equipment.csv |  |
| results/phase3/seg_identification_objects_by_analysis_result.csv |  |
| results/phase3/seg_identification_segments_by_analysis_result.csv |  |
| results/phase3/seg_series_status.csv |  |
| results/release/COMMANDS.md |  |
| results/submission/00_cover_letter.md |  |
| results/submission/04_tables.md |  |
| results/submission/05_figure_legends.md |  |
| results/submission/06_supplementary.md |  |
| results/submission/checklist_sweep.md |  |
| results/submission/docx/00_cover_letter.docx |  |
| results/submission/docx/01_title_page.docx |  |
| results/submission/docx/02_manuscript_full.docx |  |
| results/submission/docx/03_manuscript_blinded.docx |  |
| results/submission/docx/04_tables.docx |  |
| results/submission/docx/05_figure_legends.docx |  |
| results/submission/docx/06_supplementary.docx |  |
| results/submission/docx/reference.docx |  |
| results/submission/figures/Fig1.eps |  |
| results/submission/figures/Fig1.pdf |  |
| results/submission/figures/Fig1.png |  |
| results/submission/figures/Fig2.eps |  |
| results/submission/figures/Fig2.pdf |  |
| results/submission/figures/Fig2.png |  |
| results/submission/figures/Fig3.eps |  |
| results/submission/figures/Fig3.pdf |  |
| results/submission/figures/Fig3.png |  |
| results/submission/figures/Fig4.eps |  |
| results/submission/figures/Fig4.pdf |  |
| results/submission/figures/Fig4.png |  |
| results/submission/figures/Fig5.eps |  |
| results/submission/figures/Fig5.pdf |  |
| results/submission/figures/Fig5.png |  |
| results/submission/figures/Fig6.eps |  |
| results/submission/figures/Fig6.pdf |  |
| results/submission/figures/Fig6.png |  |
| results/submission/gate.json |  |
| results/table1_writers.md |  |
| results/typecheck/ceiling_summary.json |  |
| results/typecheck/docbook_quotes.json |  |

## 3. Broken derivations

`derived_from` references to row ids that do not exist. The check is the rule
`tests/test_ledger.py::test_derived_from_resolves_to_real_ids` enforces, run
here over the same file.

**0 broken references.**

None.

## 4. Retirement chains

A retired claim is never deleted, so the chain from the withdrawn wording to its
replacement has to lead somewhere. **8 RETIRED rows, 2 with no successor
named.**

| id | claim | superseded_by | successor exists | successor status | reason |
|---|---|---|---|---|---|
| C3-06-air | The IHE AI Results profile section 6.5.3.1 is the normat ... | C3-14 | yes | PENDING | AIR is Trial Implementation and has been for years, with no Connectathon test case and no Gazelle test plan. A profile at that status cannot carry a c ... |
| C3-02-prev | The majority of derived series declare a general purpose ... | C3-02 | yes | MEASURED | Not false, but not exhaustive, and the omission changed the argument. Two non-complementary shares leave 11.5 percent of the population unreported, an ... |
| PA-03-prev | The published state of the art in validating a public DI ... | PA-03 | yes | LITERATURE | An overstatement that a reviewer catches by opening one file. It is true of RunDciodvfyByCollection.pl and of the 2018 paper, but Posda has a named wo ... |
| PA-05 | The brief's characterisation of the peer-reviewed GSPS l ... | (none) | no | (none) | Wrong in both directions. It omits at least Church et al. 2026, Swinburne et al. 2025, Fischer et al. 2015 and two Eichelberg-group SPIE papers, and H ... |
| PRE-01 | Pre-registered prediction. Claim 1 will return largely n ... | (none) | no | (none) | Falsified by measurement. Key Object Selection Document Storage returns a 100.00 percent net error-class rate against a predicted null, confirmed by t ... |
| STD-02-hyp | Segmentation objects declaring SegmentAlgorithmType AUTO ... | STD-02 | yes | VERIFIED | Refuted against PS3.3 2026c. In the Segmentation IOD (0062,0007) is Type 3 with no condition attached, so omitting it is conformant and no validator c ... |
| STD-06-untested | IHE AIR has no Connectathon test case and no Gazelle tes ... | STD-06 | yes | VERIFIED | Refuted by primary sources. Gazelle Test Management holds 22 AIR test definitions with numbered steps and monitor instructions, and the IHE Connectath ... |
| F1-03-prev | dicom-validator returns an identical six-class set for b ... | F1-03 | yes | MEASURED | An artefact of this project's own parser. It captured only indented findings, and dicom-validator indents a finding by one level only when the tag has ... |

## 5. Pre-registration status

Reported, never edited. A pre-registration is worth carrying only if an outcome
lands against it, so the column that matters is the last one. An outcome counts
as recorded when the row leaves PENDING, or carries a verification date, or
states an n.

**7 PRE-* rows, 2 with an outcome recorded, 0 with an outcome proposed by a
track and not yet merged.** A proposal is not a record: the last column names
the file it is sitting in.

| id | section | status | claim | registered value | outcome recorded | outcome proposed |
|---|---|---|---|---|---|---|
| PRE-02 | V | PENDING | Writer-aware scoring. Every axis-2 result is labelled IN ... | pre-registered before any object was validate ... | no | no |
| PRE-03 | V | PENDING | Claim 2 adjudication rule. Where validators disagree, th ... | pre-registered before any object was validate ... | no | no |
| PRE-04 | V | PENDING | Standard-edition control. One edition is pinned, dicom-v ... | ContentCreatorName (0070,0084) is the named sensitivity attribute: Type 2 in older edition ... | no | no |
| PRE-05 | V | PENDING | Claim 1 threshold, set before the data. PRE-01 predicted ... | null is defined as a post-floor failure rate at or below 5 percent of series in a class; s ... | no | no |
| PRE-06 | V | MEASURED | Sampling frame, fixed before seeing which strata look in ... | drawn 5,941 series, 129.77 GB exact against a 150 GB budget; recorded 5,941 series, 6,386 ... | yes | no |
| PRE-07 | V | PENDING | Manual verification sample. The panel is entirely automa ... | order 200 series, stratified by object class, writing toolkit and disagreement class, seed ... | no | no |
| PRE-01 | PRE | RETIRED | Pre-registered prediction. Claim 1 will return largely n ... | predicted before any archive object was validate ... | yes | no |

## 6. Floor coverage

The project rule is that a failure rate quoted without its floor is not a
number. Which rows quote a rate is decided by
`colophon.ledger.rates_without_floor`, not by a second copy of the rule here.

**108 MEASURED rows quote a rate. 0 of them name no floor.** A rate with no
floor is not a number, so the second figure is the one that has to stay at zero.

| id | status | value | floor named | floor |
|---|---|---|---|---|
| P0-09 | MEASURED | 1,032,911 of 1,032,911 rows rea ... | yes | not applicable, no validator involve ... |
| P0-10 | MEASURED | derived 481,750 series; analysis-result attributed 463,543, 96.22 perc ... | yes | not applicable, no validator involve ... |
| P0-11 | MEASURED | 1.0477 instances per series; 22,977 of 504,727 instances missed, 4.55 ... | yes | not applicable, no validator involve ... |
| C3-01 | MEASURED | Manufacturer populated on 481,331 of 481,750 series, ManufacturerModel ... | yes | not applicable, no validator involved. This claim is scored ... |
| C3-02 | MEASURED | encoding library only 416,427 (86.44 percent); producing entity and co ... | yes | not applicable, no validator involved. This claim is scored ... |
| C3-03 | MEASURED | 21,721 of 481,750 series, 4.51 percent, name producer and converter bo ... | yes | not applicable, no validator involved. This claim is scored ... |
| C3-10 | MEASURED | encoding library as manufacturer 417,623 (86.69 percent); producing la ... | yes | not applicable, no validator involved. This claim is scored ... |
| C3-05 | MEASURED | 434,341 series across 16 analysis results of at least 100 series have ... | yes | not applicable, no validator involved. This claim is scored ... |
| C3-07 | MEASURED | 9,971 of 475,537 eligible series, 2.1 percent, inherited within collec ... | yes | not applicable, no validator involved. This claim is scored ... |
| C3-08 | MEASURED | 481,750 of 481,750 derived series classifie ... | yes | not applicable, no validator involved. This claim is scored ... |
| C3-12 | MEASURED | 481,750 series across 85 collections, 24 analysis results and 46,571 p ... | yes | not applicable, no validator involved. This claim is scored ... |
| C3-13 | MEASURED | removing collection nlst takes the rate from 86.4 to 34.81 percent; re ... | yes | not applicable, no validator involved. This claim is scored ... |
| C3-15 | MEASURED | a presence check over Type 1 attributes reports 100 percent and measur ... | yes | not applicable, no validator involved. This claim is scored ... |
| W-01 | MEASURED | dcmqi 411,865 (85.49 percent); not identifiable from index 47,826 (9.9 ... | yes | not applicable, no validator involve ... |
| W-02 | MEASURED | totalsegmentator_ct_segmentations: level 1 carries QIICR and a git URL ... | yes | not applicable, no validator involve ... |
| W-03 | MEASURED | querying the most common dcmqi spelling exactly recalls 380,712 of 411 ... | yes | not applicable, no validator involve ... |
| V-02 | MEASURED | dcmqi is declared on 411,865 of 481,750 derived series, 85.49 percen ... | yes | not applicable, this row defines the instrument rather than ... |
| STD-05 | MEASURED | non_conformant: A stated requirement of PS3; conformant_but_uninformat ... | yes | not applicable, this section defines requirements rather tha ... |
| P2P-02 | MEASURED | message_class_id cc372fb8c40c present on 0 of 10 object ... | yes | Phase 1 floor sets, results/floor_set.csv. No rate is comput ... |
| P2P-08 | MEASURED | 2 of 10 objects carry ImplementationClassUID 1.3.6.1.4.1.22213.1.143 w ... | yes | Phase 1 floor sets, results/floor_set.csv. No rate is comput ... |
| P2P-09 | MEASURED | 10 of 10 values are exactly 7 lowercase hex characters; 5 distinct val ... | yes | Phase 1 floor sets, results/floor_set.csv. No rate is comput ... |
| P2P-06 | MEASURED | present on 0 of 10 object ... | yes | Phase 1 floor sets, results/floor_set.csv. No rate is comput ... |
| P2C-02 | MEASURED | Comprehensive/nnu_net_bpr_annotations 2,906 objects err 49.5% warn 100 ... | yes | gross rates only. Phase 1 floor sets are writer-specific and ... |
| B-02 | MEASURED | SEG BINARY, dciodvfy, nine variants: Jaccard ranges from 0.0000 to 0.8 ... | yes | this section measures the floor under perturbation; it does ... |
| B-03 | MEASURED | SEG BINARY, dicom-validator, nine variants: Jaccard ranges from 0.8571 ... | yes | this section measures the floor under perturbation; it does ... |
| B-04 | MEASURED | no cell whose baseline sets differ becomes equal or reverses containme ... | yes | this section measures the floor under perturbation; it does ... |
| C-CSR-05 | MEASURED | gross 723 of 2,118 objects (34.14 percent), floor 0 (0.00 percent), ne ... | yes | 0 objects (0.00 percent) carry only FLOOR, NOT-IOD or PLAUSI ... |
| C-CSR-06 | MEASURED | gross 826 of 2,118 objects (39.00 percent), floor 594 (28.05 percent), ... | yes | 594 objects (28.05 percent) carry only FLOOR, NOT-IOD or PLA ... |
| C-CSR-07 | MEASURED | gross 2,118 of 2,118 objects (100.00 percent), floor 1,656 (78.19 perc ... | yes | 1,656 objects (78.19 percent) carry only FLOOR, NOT-IOD or P ... |
| C-CSR-08 | MEASURED | NULL 462 of 462 (100.00 percent); dicom_sr_breast_clinical 1 of 1,292 ... | yes | reported per validator in C-CSR-05, C-CSR-06 and C-CSR-07; n ... |
| C-CSR-09 | MEASURED | median 0.12 percent across 7 collections: breast_diagnosis 0.00 percen ... | yes | reported per validator in C-CSR-05, C-CSR-06 and C-CSR-0 ... |
| C-CSR-10 | MEASURED | as adjudicated, net 723 of 2,118 (34.14 percent); with the off-part cl ... | yes | see C-CSR-05 and C-CSR-0 ... |
| C-GSPS-01 | MEASURED | dciodvfy Error severity: gross 513 of 1,086 objects, 47.24 percent; fl ... | yes | the entire gross Error rate is floor: 1 class FLOOR (Lateral ... |
| C-GSPS-02 | MEASURED | dciodvfy Warning severity: gross 1,086 of 1,086 objects, 100.00 percen ... | yes | the entire gross Warning rate is floor: 2 classes NOT-IOD (D ... |
| C-GSPS-03 | MEASURED | dicom-validator: 0 distinct message classes, gross 0 of 1,086 at every ... | yes | not applicable, the validator produced no findings, so there ... |
| C-GSPS-08 | MEASURED | qiba_ct_1c 462 objects, gross Error 100.00 percent, net Error 0.00 per ... | yes | gross Error rates by collection are 100.00, 10.68 and 4.17 p ... |
| C-PM-01 | MEASURED | 345 of 345 distinct message classes adjudicated: FLOOR 9, PLAUSIBILITY ... | yes | results/floor_set.csv, highdicom built Parametric Map fixtur ... |
| C-PM-05 | MEASURED | gross / floor / net, 691 objects: dciodvfy 691 / 691 / 0; dicom-valida ... | yes | results/floor_set.csv, highdicom built Parametric Map fixtur ... |
| C-PM-06 | MEASURED | 0 residual NET classes of 345 adjudicated, and 0 left UNDECIDABL ... | yes | results/floor_set.csv, highdicom built Parametric Map fixtur ... |
| C-PM-07 | MEASURED | 0 of 691 objects carry any dciodvfy message of severity Error, and dci ... | yes | results/floor_set.csv, highdicom built Parametric Map fixtur ... |
| C-RWV-01 | MEASURED | dciodvfy Error triple, gross 20, floor 20, net 0 of 20 objects, net 0. ... | yes | the floor is the adjudication itself: FLOOR, NOT-IOD and PLA ... |
| C-RWV-02 | MEASURED | dciodvfy Warning triple, gross 20, floor 20, net 0 of 20 object ... | yes | the floor is the adjudication itself: FLOOR, NOT-IOD and PLA ... |
| C-RWV-03 | MEASURED | dicom-validator, 0 findings on 20 of 20 objects, gross 0, floor 0, net ... | yes | not applicable, there is no message to adjudicat ... |
| C-KOS-01 | MEASURED | dciodvfy Error triple, gross 40, floor 0, net 40 of 40 objects, net 10 ... | yes | the floor is the adjudication itself: FLOOR, NOT-IOD and PLA ... |
| C-KOS-02 | MEASURED | dicom-validator ERROR triple, gross 40, floor 0, net 40 of 40 objects, ... | yes | the floor is the adjudication itself: FLOOR, NOT-IOD and PLA ... |
| C-KOS-03 | MEASURED | dciodvfy Warning triple, gross 40, floor 40, net 0 of 40 object ... | yes | the floor is the adjudication itself: FLOOR, NOT-IOD and PLA ... |
| D-01 | MEASURED | dcmpschk emits 'Test passed.' on 1,086 of 1,086 GSPS objects and emits ... | yes | no dcmpschk floor exists: Phase 1 emitted no presentation st ... |
| D-03 | MEASURED | the census recorded 1,087 distinct dcmpschk message classes for this S ... | yes | no dcmpschk floor exists: Phase 1 emitted no presentation st ... |
| D-04 | MEASURED | dcmpschk flags 0 of 1,086, dicom-validator flags 0 of 1,086, dciodvfy ... | yes | no dcmpschk floor exists: Phase 1 emitted no presentation st ... |
| E-03 | MEASURED | the C3-12 encoder flag has exactly zero within-stratum variance in all ... | yes | not applicable, no validator involve ... |
| F2-02 | MEASURED | 11,128 of 28,721 objects carry equipment attributes that name no toolk ... | yes | not applicable, no validator involve ... |
| F2-03 | MEASURED | 1,292 of 1,388 scored objects disagree: Comprehensive SR Storage decla ... | yes | not applicable, no validator involve ... |
| F2-05 | MEASURED | 12 cells, 4 of them single-writer; 32 rows carrying a message class an ... | yes | this table is the floor; it does not quote a rate against on ... |
| F2-06 | MEASURED | Jaccard 0.8571, 6 shared of 7 in the unio ... | yes | this table is the floor; it does not quote a rate against on ... |
| F2-07 | MEASURED | dciodvfy e4c7fa2d56f7: Grayscale Softcopy Presentation State Storage 4 ... | yes | this table is the floor; it does not quote a rate against on ... |
| F2-08 | MEASURED | complete: Real World Value Mapping Storage 20 series; Key Object Selec ... | yes | not applicable, no validator involve ... |
| F3-02 | MEASURED | 13 of 296 rows have no artefact on disk; 195 of 296 are named by no re ... | yes | not applicable, no validator is involved and no conformance ... |
| F3-03 | MEASURED | 85 of 210 scanned files are named by no source_file in the ledge ... | yes | not applicable, no validator is involved and no conformance ... |
| F3-05 | MEASURED | 8 RETIRED rows, 8 carry a reason, 6 name a successor, 6 of those succe ... | yes | not applicable, no validator is involved and no conformance ... |
| F3-07 | MEASURED | 108 rows quote a rate by the ledger's own rule, 0 of them name no floo ... | yes | not applicable, no validator is involved and no conformance ... |
| F3-08 | MEASURED | 160 of 296 rows name a test, 142 distinct tests, 0 name a test that do ... | yes | not applicable, no validator is involved and no conformance ... |
| G2-02 | MEASURED | 5 of 138 query rows carry a hit count captured at search time; 133 do ... | yes | not applicable, no validator involve ... |
| G2-03 | MEASURED | condition (a) met for 5 of 138 query rows; condition (b) met for 4 scr ... | yes | not applicable, no validator involve ... |
| G2-04 | MEASURED | 132 of 138 query rows were issued against a general web search whose e ... | yes | not applicable, no validator involve ... |
| G2-06 | MEASURED | 5 of 6 included records have no matching URL in colophon.prior_art.RET ... | yes | not applicable, no validator involve ... |
| G2-07 | MEASURED | 0 recorded retrievals of Posda source code or database schema; PA-08 a ... | yes | not applicable, no validator involve ... |
| F1-M-01 | MEASURED | 2,806 words in the Methods body excluding two display tables and the a ... | yes | not applicable, this row records a document rather than a ra ... |
| F4-01 | MEASURED | 26,405 of 291,604 manifest series recorded; 26,405 lines read and 0 sk ... | yes | not applicable, this row counts coverage and does not quote ... |
| F4-02 | MEASURED | 5,408 of 5,408 series recorded, 0 of 5,408 objects adjudicated, 0 adju ... | yes | none exists for this class: no message class has been adjudi ... |
| C-C3D-06 | MEASURED | gross 1,801 of 5,408 objects (33.30 percent), floor 0 (0.00 percent), ... | yes | 0 objects (0.00 percent) carry only FLOOR, NOT-IOD or PLAUSI ... |
| C-C3D-07 | MEASURED | gross 5,408 of 5,408 objects (100.00 percent), floor 5,408 (100.00 per ... | yes | 5,408 objects (100.00 percent) carry only FLOOR, NOT-IOD or ... |
| C-C3D-08 | MEASURED | gross 1,892 of 5,408 objects (34.99 percent), floor 91 (1.68 percent), ... | yes | 91 objects (1.68 percent) carry only FLOOR, NOT-IOD or PLAUS ... |
| C-C3D-09 | MEASURED | lung_pet_ct_dx_annotations 38 of 1,091 (3.48 percent); nlst_sybil 325 ... | yes | reported per validator in C-C3D-06, C-C3D-07 and C-C3D-08; n ... |
| C-C3D-10 | MEASURED | median 3.48 percent across 5 collections: lung_pet_ct_dx 3.48 percent ... | yes | reported per validator in C-C3D-06, C-C3D-07 and C-C3D-0 ... |
| C-C3D-11 | MEASURED | as adjudicated: net 1,801 of 5,408 (33.30 percent), collection median ... | yes | see C-C3D-06 and C-C3D-0 ... |
| P3-01 | MEASURED | 34,234 of 36,488 non-MANUAL segments, 93.82 percent, carry no identifi ... | yes | not applicable, no validator is involved: this is an attribu ... |
| P3-02 | MEASURED | 0 of 36,488 non-MANUAL segments, 0.00 percent, carry a present but inc ... | yes | not applicable, no validator is involved: this is an attribu ... |
| P3-03 | MEASURED | 0 of 36,488 non-MANUAL segments, 0.00 percen ... | yes | not applicable, no validator is involved: this is an attribu ... |
| P3-11 | MEASURED | 25 segments carry a SegmentAlgorithmType that is none of AUTOMATIC, SE ... | yes | none subtracted. The class is not in any Phase 1 floor set, ... |
| C3T-00 | MEASURED | non-conformant 1,403, 4.00 percent; conformant but uninformative 28,90 ... | yes | not applicable, no validator is involved: these are attribut ... |
| C3T-08 | MEASURED | DeviceSerialNumber (0018,1000) is absent on 966 and zero-length on 397 ... | yes | none subtracted. This is a Type 1 presence violation read di ... |
| C3T-02 | MEASURED | encoder-only bucket: 4,713 of 35,107 objects, 13.42 percent object wei ... | yes | not applicable, no validator is involved: these are attribut ... |
| C3T-04 | MEASURED | dcmqi 32,963 of 32,963 non-MANUAL segments absent; not identifiable fr ... | yes | not applicable, no validator is involved: these are attribut ... |
| C3T-07 | MEASURED | 7,004 of 35,107 objects relabelled, 19.95 percent object weighted; by ... | yes | not applicable, no validator is involved: these are attribut ... |
| ADJ2-01 | MEASURED | three-way crosswalked agreement 84.35 percent, kappa 0.5929 over 2,256 ... | yes | not applicable, this row measures adjudication stability rat ... |
| ADJ2-02 | MEASURED | 90.56 percent agreement, kappa 0.6352 over 2,256 classes; blind subset ... | yes | not applicable, this row measures adjudication stabilit ... |
| ADJ2-03 | MEASURED | Real World Value Mapping Storage pass1 0.00 percent, pass2 0.00, conse ... | yes | measured above the classes both passes agreed were floor. Cl ... |
| DEV-01 | MEASURED | the two builds are known to differ on three changelog entries, all con ... | yes | not applicable, these rows measure exposure to a tool versio ... |
| DEV-02 | MEASURED | registered 0.28.0, installed 0.28.1; no module that produces a measure ... | yes | not applicable, these rows measure exposure to a tool versio ... |
| C3T-09 | MEASURED | permissive reading, any token that is neither a published sentinel nor ... | yes | not applicable, no validator is involved: this is an attribu ... |
| C3T-10 | MEASURED | RT Structure Set Storage is 19,358 of 35,107 objects, 55.14 percent of ... | yes | not applicable, no validator is involve ... |
| REF-01 | MEASURED | 38 references; 38 of 38 cited at least once; 0 markers that resolve to ... | yes | not applicable, this row reports a documentary check and not ... |
| FIG-02 | MEASURED | 11 of the 21 silent cells are Segmentation Storage; 5 are entirely MAN ... | yes | not applicable, this row counts analysis-result cells and no ... |
| FIG-04 | MEASURED | 6 of 6 figures draw no title; 6 of 6 return one for the legend; the tw ... | yes | not applicable, this row reports a property of the figure se ... |
| FIG-05 | MEASURED | 88 text pairings logged, lowest 5.10 to 1, against a required 4.5 to 1 ... | yes | not applicable, this row reports a rendering property and no ... |
| FIG-06 | MEASURED | 6 of 6 figures at 174.0 mm; before this was checked, figure 1 was 174, ... | yes | not applicable, this row reports a rendering property and no ... |
| C3T-11 | MEASURED | 4 of 31 cells carry a version. totalsegmentator_ct_segmentations now r ... | yes | not applicable, this row reports a published value rather th ... |
| DEV-03 | MEASURED | 7,100 highdicom-written objects: 1,788 carry a conversion-pipeline rep ... | yes | not applicable, this row counts attribute values and not val ... |
| SUB-07 | MEASURED | EPS 6 of 6 identical, PDF 12 of 12 identical, PNG 12 of 12 identical, ... | yes | not applicable, this row compares bytes rather than quoting ... |
| SUB-08 | MEASURED | 19 rows in the computed table, 19 carrying a count, ratio, diff or mat ... | yes | not applicable, this row reports a property of a checklis ... |
| DISC-01 | MEASURED | 0 matching objects of 104,774 searched, across all nine SOP classes re ... | yes | not applicable, this row counts attribute values and not val ... |
| DISC-02 | MEASURED | 933 sentences scanned across 10 documents; 168 assert an absence or a ... | yes | not applicable, this row counts sentence ... |
| SUB-10 | MEASURED | 261 tracked files, 12.1 MB, 0 DICOM objects. Excluded: the census reco ... | yes | not applicable, this row measures a repositor ... |
| C3T-12 | MEASURED | 6 of 36 cells carry `(null)`, holding 5,731 of 35,107 objects, 16.32 p ... | yes | not applicable, this row counts analysis-result cell ... |
| C3T-13 | MEASURED | 7 classes censused completely, so their cells are the frame's. Segment ... | yes | not applicable, this row reports coverage of a uni ... |
| SUB-11 | MEASURED | 11 assertions, up from 10. Strengthened: N-of-M pairs recompute from t ... | yes | not applicable, this row counts assertion ... |
| SUB-12 | MEASURED | 6 of 6 figures cited in both manuscript copies, first-citation order 1 ... | yes | not applicable, this row counts citation ... |
| SUB-13 | MEASURED | 7 of 7 documents converted with pypandoc-binary 1.15 carrying pandoc 3 ... | yes | not applicable, this row reports format checks and not a val ... |

## 7. Test coverage

`pinned_by_test` is what stops a claim regressing silently, so the field is
worth only as much as the test behind it. **161 rows name a test, 143 distinct
tests, 0 rows name a test that does not exist, 0 rows whose test did not
pass.**

| id | test | exists | result |
|---|---|---|---|
| P0-01 | tests/test_phase0.py::test_index_shape | yes | PASSED |
| P0-02 | tests/test_phase0.py::test_derived_totals | yes | PASSED |
| P0-05 | tests/test_phase0.py::test_gsps_split | yes | PASSED |
| P0-10 | tests/test_phase0.py::test_two_denominators | yes | PASSED |
| P0-11 | tests/test_phase0.py::test_first_file_coverage | yes | PASSED |
| C3-01 | tests/test_phase0.py::test_provenance_population | yes | PASSED |
| C3-02 | tests/test_phase0.py::test_buckets_are_exhaustive | yes | PASSED |
| C3-03 | tests/test_phase0.py::test_positive_control | yes | PASSED |
| C3-11 | tests/test_phase0.py::test_largest_analysis_result | yes | PASSED |
| C3-04 | tests/test_phase0.py::test_dcmqi_spellings | yes | PASSED |
| C3-12 | tests/test_phase0.py::test_clustering | yes | PASSED |
| C3-13 | tests/test_phase0.py::test_leave_one_out | yes | PASSED |
| C3-15 | tests/test_phase0.py::test_provenance_population | yes | PASSED |
| W-01 | tests/test_writers.py::test_writer_census | yes | PASSED |
| W-02 | tests/test_writers.py::test_carrier_hierarchy | yes | PASSED |
| W-03 | tests/test_writers.py::test_cohort_recall | yes | PASSED |
| W-04 | tests/test_writers.py::test_sentinels_published | yes | PASSED |
| V-01 | tests/test_panel.py::test_every_class_has_both_axes | yes | PASSED |
| V-08 | tests/test_panel.py::test_panel_is_not_uniform | yes | PASSED |
| V-09 | tests/test_panel.py::test_excluded_tools_carry_a_reason_and_a_consequence | yes | PASSED |
| STD-01 | tests/test_standards.py::test_macro_tags | yes | PASSED |
| STD-02 | tests/test_standards.py::test_segmentation_hypothesis_is_dead | yes | PASSED |
| STD-03 | tests/test_standards.py::test_surviving_hooks | yes | PASSED |
| STD-04 | tests/test_standards.py::test_enhanced_general_equipment | yes | PASSED |
| STD-06 | tests/test_standards.py::test_air_is_normative_and_tested | yes | PASSED |
| F1-01 | tests/test_floor.py::test_headline_overlap | yes | PASSED |
| F1-04 | tests/test_floor.py::test_emission_gaps_recorded | yes | PASSED |
| F1-05 | tests/test_floor.py::test_sr_sop_classes_differ | yes | PASSED |
| F1-06 | tests/test_floor.py::test_exit_status_is_not_a_verdict | yes | PASSED |
| F1-07 | tests/test_floor.py::test_both_severity_forms_match | yes | PASSED |
| F1-09 | tests/test_floor.py::test_content_equality | yes | PASSED |
| P2P-01 | tests/test_pilot.py::test_pilot_shape | yes | PASSED |
| P2P-02 | tests/test_pilot.py::test_target_message_class | yes | PASSED |
| P2P-04 | tests/test_pilot.py::test_provenance_states | yes | PASSED |
| P2P-05 | tests/test_pilot.py::test_file_meta_names_dcmtk | yes | PASSED |
| P2P-09 | tests/test_pilot.py::test_software_versions_are_commit_hashes | yes | PASSED |
| P2P-06 | tests/test_pilot.py::test_contributing_equipment | yes | PASSED |
| F1-10 | tests/test_floor.py::test_unindented_findings_are_not_dropped | yes | PASSED |
| P2C-01 | tests/test_census.py::test_no_partial_class_is_reported | yes | PASSED |
| P2C-03 | tests/test_census.py::test_three_state_provenance | yes | PASSED |
| B-01 | tests/test_variants.py::test_baseline_reproduces_phase_one | yes | PASSED |
| B-02 | tests/test_variants.py::test_dciodvfy_ladder_jaccards | yes | PASSED |
| B-03 | tests/test_variants.py::test_dicom_validator_ladder_jaccards | yes | PASSED |
| B-04 | tests/test_variants.py::test_direction_never_flips | yes | PASSED |
| B-05 | tests/test_variants.py::test_deflate_is_a_reader_failure_not_an_iod_finding | yes | PASSED |
| B-06 | tests/test_variants.py::test_not_applicable_cells_are_recorded | yes | PASSED |
| B-07 | tests/test_variants.py::test_round_trip_control_moves_nothing | yes | PASSED |
| B-08 | tests/test_variants.py::test_single_writer_classes_carry_no_jaccard | yes | PASSED |
| B-09 | tests/test_variants.py::test_sr_baseline_is_degenerate_for_the_flip_test | yes | PASSED |
| B-10 | tests/test_variants.py::test_residue_is_stable_under_perturbation | yes | PASSED |
| C-RWV-01 | tests/test_adjudicate_rwv_kos.py::test_the_triples_are_pinned | yes | PASSED |
| C-RWV-02 | tests/test_adjudicate_rwv_kos.py::test_the_triples_are_pinned | yes | PASSED |
| C-RWV-03 | tests/test_adjudicate_rwv_kos.py::test_the_triples_are_pinned | yes | PASSED |
| C-RWV-04 | tests/test_adjudicate_rwv_kos.py::test_every_message_class_is_adjudicated | yes | PASSED |
| C-RWV-05 | tests/test_adjudicate_rwv_kos.py::test_every_message_class_is_adjudicated | yes | PASSED |
| C-RWV-06 | tests/test_adjudicate_rwv_kos.py::test_every_message_class_is_adjudicated | yes | PASSED |
| C-RWV-07 | tests/test_adjudicate_rwv_kos.py::test_every_message_class_is_adjudicated | yes | PASSED |
| C-KOS-01 | tests/test_adjudicate_rwv_kos.py::test_the_triples_are_pinned | yes | PASSED |
| C-KOS-02 | tests/test_adjudicate_rwv_kos.py::test_the_triples_are_pinned | yes | PASSED |
| C-KOS-03 | tests/test_adjudicate_rwv_kos.py::test_the_triples_are_pinned | yes | PASSED |
| C-KOS-04 | tests/test_adjudicate_rwv_kos.py::test_no_net_without_a_section_and_a_table | yes | PASSED |
| C-RWV-08 | tests/test_adjudicate_rwv_kos.py::test_pre05_inputs_are_pinned | yes | PASSED |
| C-KOS-05 | tests/test_adjudicate_rwv_kos.py::test_pre05_inputs_are_pinned | yes | PASSED |
| D-01 | tests/test_gsps_dcmpschk.py::test_pass_count_is_pinned | yes | PASSED |
| D-02 | tests/test_gsps_dcmpschk.py::test_pass_line_is_never_a_finding | yes | PASSED |
| D-03 | tests/test_gsps_dcmpschk.py::test_banner_is_not_a_finding | yes | PASSED |
| D-04 | tests/test_gsps_dcmpschk.py::test_cross_validator_direction | yes | PASSED |
| E-01 | tests/test_sample.py::test_strata_partition | yes | PASSED |
| E-02 | tests/test_sample.py::test_registered_n_properties | yes | PASSED |
| E-03 | tests/test_sample.py::test_planning_icc | yes | PASSED |
| E-04 | tests/test_sample.py::test_floor_coverage | yes | PASSED |
| E-05 | tests/test_sample.py::test_every_stratum_has_a_rule | yes | PASSED |
| E-06 | tests/test_sample.py::test_clustering_dominates | yes | PASSED |
| E-07 | tests/test_sample.py::test_execute_guard_blocks_a_draw | yes | PASSED |
| F2-01 | tests/test_tables.py::test_object_counts_match_the_census | yes | PASSED |
| F2-02 | tests/test_tables.py::test_no_incomplete_class_in_table1 | yes | PASSED |
| F2-03 | tests/test_tables.py::test_disagreement_rests_on_a_registered_expectation | yes | PASSED |
| F2-04 | tests/test_tables.py::test_identity_spread_is_reported | yes | PASSED |
| F2-05 | tests/test_tables.py::test_single_writer_cells_are_marked | yes | PASSED |
| F2-06 | tests/test_tables.py::test_seg_binary_jaccard_is_the_corrected_value | yes | PASSED |
| F2-07 | tests/test_tables.py::test_corpus_context_is_bounded | yes | PASSED |
| F2-08 | tests/test_tables.py::test_no_incomplete_class_in_table1 | yes | PASSED |
| F2-09 | tests/test_tables.py::test_scan_reports_skipped_lines | yes | PASSED |
| F2-10 | tests/test_tables.py::test_equipment_rule_is_reused_verbatim | yes | PASSED |
| F3-01 | tests/test_claims_map.py::test_every_ledger_row_is_mapped | yes | PASSED |
| F3-02 | tests/test_claims_map.py::test_orphans_are_reported_not_hidden | yes | not run |
| F3-03 | tests/test_claims_map.py::test_uncited_artefacts_are_reported | yes | not run |
| F3-04 | tests/test_claims_map.py::test_no_broken_derivations | yes | PASSED |
| F3-05 | tests/test_claims_map.py::test_retired_rows_keep_a_reason | yes | PASSED |
| F3-06 | tests/test_claims_map.py::test_pre_rows_are_reported_unchanged | yes | PASSED |
| F3-07 | tests/test_claims_map.py::test_floor_rule_is_the_ledgers_own | yes | PASSED |
| F3-08 | tests/test_claims_map.py::test_named_tests_exist | yes | PASSED |
| G2-01 | tests/test_prisma.py::test_prisma_s_items_are_all_answered | yes | PASSED |
| G2-02 | tests/test_prisma.py::test_no_row_claims_an_uncaptured_hit_count | yes | PASSED |
| G2-03 | tests/test_prisma.py::test_the_auditability_rule_is_stated_and_applied | yes | PASSED |
| G2-04 | tests/test_prisma.py::test_web_search_rows_never_state_a_hit_count | yes | PASSED |
| G2-05 | tests/test_prisma.py::test_every_gap_reaches_the_appendix | yes | PASSED |
| G2-06 | tests/test_prisma.py::test_included_records_are_checked_against_the_retrieval_log | yes | PASSED |
| G2-07 | tests/test_prisma.py::test_grey_literature_is_reported_as_unsystematic | yes | PASSED |
| G3-01 | tests/test_standards.py::test_air_is_normative_and_tested | yes | PASSED |
| G3-02 | tests/test_standards.py::test_air_table_6531_1_is_a_map_not_a_requirement | yes | PASSED |
| G3-03 | tests/test_standards.py::test_air_table_6531_1_is_a_map_not_a_requirement | yes | PASSED |
| G3-04 | tests/test_standards.py::test_air_table_6531_1_is_a_map_not_a_requirement | yes | PASSED |
| G3-05 | tests/test_standards.py::test_air_table_6531_1_is_a_map_not_a_requirement | yes | PASSED |
| F4-01 | tests/test_results_doc.py::test_no_partial_class_carries_a_rate | yes | PASSED |
| F4-02 | tests/test_results_doc.py::test_unadjudicated_class_carries_no_rate | yes | PASSED |
| F4-03 | tests/test_results_doc.py::test_every_number_in_the_results_draft_is_backed | yes | PASSED |
| F4-05 | tests/test_results_doc.py::test_the_guard_can_fail | yes | PASSED |
| P3-01 | tests/test_phase3.py::test_object_rollup_keeps_absence_and_incompleteness_apart | yes | PASSED |
| P3-02 | tests/test_phase3.py::test_sequence_missing_a_type1_child_reads_as_incomplete | yes | PASSED |
| P3-03 | tests/test_phase3.py::test_zero_item_sequence_is_its_own_state | yes | PASSED |
| P3-06 | tests/test_phase3.py::test_state_separates_absent_from_zero_length | yes | PASSED |
| P3-07 | tests/test_phase3.py::test_severity_matches_both_documented_forms | yes | PASSED |
| P3-12 | tests/test_phase3.py::test_writer_relabel_reuses_the_phase0_rule_table | yes | PASSED |
| P3-09 | tests/test_phase3.py::test_dcmpschk_is_not_used_on_segmentation | yes | PASSED |
| C3T-00 | tests/test_claim3.py::test_grades_are_exhaustive_and_mutually_exclusive | yes | PASSED |
| C3T-01 | tests/test_claim3.py::test_three_states_never_summed | yes | PASSED |
| C3T-08 | tests/test_claim3.py::test_type1_violations_are_corroborated | yes | PASSED |
| C3T-02 | tests/test_claim3.py::test_buckets_are_exhaustive | yes | PASSED |
| C3T-03 | tests/test_claim3.py::test_ladder_levels_are_the_registered_five | yes | PASSED |
| C3T-04 | tests/test_claim3.py::test_absence_and_incompleteness_stay_apart | yes | PASSED |
| C3T-07 | tests/test_claim3.py::test_writer_rule_table_is_imported_not_restated | yes | PASSED |
| ADJ2-01 | tests/test_adjudicate2.py::test_agreement_is_reported_both_ways | yes | PASSED |
| ADJ2-02 | tests/test_adjudicate2.py::test_consensus_only_keeps_agreements | yes | PASSED |
| ADJ2-03 | tests/test_adjudicate2.py::test_consensus_never_exceeds_either_pass | yes | PASSED |
| DEV-01 | tests/test_deviations.py::test_pin_exposure_is_measured | yes | PASSED |
| DEV-02 | tests/test_deviations.py::test_highdicom_is_not_in_the_measurement_path | yes | PASSED |
| STD-07 | tests/test_typecheck.py::test_every_type_reproduces | yes | PASSED |
| STD-08 | tests/test_typecheck.py::test_the_ceiling_has_three_tiers | yes | PASSED |
| PA-10 | tests/test_prior_art.py::test_europe_pmc_negative_is_recorded | yes | PASSED |
| PA-11 | tests/test_prior_art.py::test_cp_negative_covers_the_whole_series | yes | PASSED |
| STD-09 | tests/test_typecheck.py::test_the_two_attributes_are_adjacent_rows_of_C_8_20_2 | yes | PASSED |
| C3T-10 | tests/test_manuscript_tables.py::test_leave_one_class_out_is_reported | yes | PASSED |
| FIG-01 | tests/test_figures.py::test_every_annotated_value_is_in_the_ledger | yes | PASSED |
| REF-01 | tests/test_references.py::test_every_entry_carries_a_resolvable_identifier | yes | PASSED |
| REF-04 | tests/test_references.py::test_the_air_quotation_is_at_the_revision_and_page_the_discussion_names | yes | PASSED |
| REF-05 | tests/test_references.py::test_the_standards_rows_match_the_pinned_status_table | yes | PASSED |
| REF-06 | tests/test_references.py::test_the_standards_rows_match_the_pinned_status_table | yes | PASSED |
| FM-02 | tests/test_references.py::test_the_front_matter_leaves_its_unknowns_as_fields | yes | PASSED |
| CPD-01 | tests/test_results_doc.py::test_the_correction_proposal_is_not_filed_until_it_says_so | yes | PASSED |
| REF-07 | tests/test_references.py::test_every_entry_carries_a_resolvable_identifier | yes | PASSED |
| SUB-01 | tests/test_submission.py::test_the_checklist_records_no_unmet_requirement | yes | PASSED |
| SUB-03 | tests/test_submission.py::test_the_abstract_is_within_the_word_limit | yes | PASSED |
| SUB-04 | tests/test_submission.py::test_the_blinded_copy_leaks_nothing_a_plain_search_would_find | yes | PASSED |
| SUB-05 | tests/test_submission.py::test_the_supplementary_index_points_at_files_that_exist | yes | PASSED |
| FIG-04 | tests/test_figures.py::test_no_figure_draws_a_title_or_a_caption | yes | PASSED |
| FIG-05 | tests/test_figures.py::test_every_lettering_pair_clears_the_contrast_minimum | yes | PASSED |
| FIG-06 | tests/test_figures.py::test_figure_width_is_measured_off_the_shipped_file_not_the_canvas | yes | PASSED |
| C3T-11 | tests/test_manuscript_tables.py::test_no_manuscript_table_prints_nan | yes | PASSED |
| SUB-06 | tests/test_submission.py::test_every_number_in_the_package_is_backed | yes | not run |
| SUB-07 | tests/test_addendum04.py::test_the_figure_set_reproduces_across_processes | yes | PASSED |
| SUB-08 | tests/test_addendum04.py::test_no_automatic_checklist_row_states_a_reason_instead_of_a_count | yes | PASSED |
| DISC-01 | tests/test_addendum04.py::test_the_company_search_reports_what_it_could_not_search | yes | PASSED |
| DISC-02 | tests/test_addendum04.py::test_the_absence_sweep_runs_and_reports_rather_than_edits | yes | PASSED |
| SUB-09 | tests/test_addendum04.py::test_a_final_package_refuses_while_a_field_is_empty | yes | PASSED |
| SUB-10 | tests/test_addendum04.py::test_the_release_metadata_exists_and_the_snapshot_is_stated | yes | PASSED |
| CPD-04 | tests/test_addendum04.py::test_the_manuscript_never_types_the_proposal_status | yes | PASSED |
| SUB-11 | tests/test_addendum04.py::test_no_automatic_checklist_row_states_a_reason_instead_of_a_count | yes | PASSED |
| SUB-14 | tests/test_submission.py::test_the_employment_disclosure_names_the_two_works_it_says_it_names | yes | PASSED |
| REL-04 | tests/test_references.py::test_every_version_string_derives_from_one_source | yes | PASSED |
| SUB-15 | tests/test_submission.py::test_no_identifier_of_any_shape_reaches_the_blinded_copy | yes | PASSED |

Tests were not run in this pass, so 3 rows report their result as not run.

## What was dropped

Nothing was sampled. Every row in `results/ledger.csv` is mapped and every file
under `results/` is inventoried. Three exclusions, all stated above and all
applied by rule rather than by hand: `results/ledger.csv` and the map's own two
outputs are excluded from the carrier scan, and `results/pending_ledger/` is
excluded from both the carrier scan and the uncited count. Claim text is
truncated to 56 characters. The pinned tests were not run in this pass.
