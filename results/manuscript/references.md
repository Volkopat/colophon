# References

Grouped by kind and numbered within the list as a whole, because the groups are
what a reader of this paper checks: the literature, the standard and the
documents that change it, the tools at the versions that ran, and the prior work
this study extends. The submission package renumbers this list by order of first
citation and re-renders it in the venue's style, from the same entries, so the
two forms cannot disagree about what a reference says.

Every entry carries a resolvable identifier: a DOI where one exists, otherwise a
URL with the date it was retrieved. Entries for documents that are pinned by
content hash elsewhere in this repository carry that hash, so a reader can
establish that the document quoted is the document that was read.

**This file is generated.** `colophon/references.py` holds the entries, the
Crossref cache holds the bibliographic fields, and the pinned DICOM status table
holds every Correction Proposal status. Edit the module, not this file.
`tests/test_references.py` asserts that every bracketed citation in the
manuscript resolves to an entry here, that every entry here is cited at least
once, and that no bare surname citation remains.

## Literature

1. Longpre S, Mahari R, Chen A, Obeng-Marnu N, Sileo D, Brannon W, et al. A
   large-scale audit of dataset licensing and attribution in AI. Nature
   Machine Intelligence. 2024;6(8):975-987. doi:10.1038/s42256-024-00878-8.

2. Huang YN, Jaiswal PV, Rajes A, Yadav A, Yu D, Liu F, et al. The systematic
   assessment of completeness of public metadata accompanying omics studies in
   the Gene Expression Omnibus data repository. Genome Biology.
   2025;26(1):274. doi:10.1186/s13059-025-03725-0.

3. Clark K, Vendt B, Smith K, Freymann J, Kirby J, Koppel P, et al. The Cancer
   Imaging Archive (TCIA): Maintaining and Operating a Public Information
   Repository. Journal of Digital Imaging. 2013;26(6):1045-1057.
   doi:10.1007/s10278-013-9622-7.

4. Prior F, Smith K, Sharma A, Kirby J, Tarbox L, Clark K, et al. The public
   cancer radiology imaging collections of The Cancer Imaging Archive.
   Scientific Data. 2017;4(1):170124. doi:10.1038/sdata.2017.124.

5. Bennett W, Smith K, Jarosz Q, Nolan T, Bosch W. Reengineering Workflow for
   Curation of DICOM Datasets. Journal of Digital Imaging. 2018;31(6):783-791.
   doi:10.1007/s10278-018-0097-4.

6. Fedorov A, Longabaugh WJR, Pot D, Clunie DA, Pieper S, Aerts HJWL, et al.
   NCI Imaging Data Commons. Cancer Research. 2021;81(16):4188-4193.
   doi:10.1158/0008-5472.CAN-21-0950.

7. Krishnaswamy D, Thiriveedhi VK, Ciausu C, Clunie D, Pieper S, Kikinis R, et
   al. Rule-based outlier detection of AI-generated anatomy segmentations.
   arXiv:2406.14486 [eess.IV]. 2024. doi:10.48550/arXiv.2406.14486. Cited as
   the preprint because no journal or proceedings version was found at the
   time of writing.

## The standard, and the documents that change it

8. National Electrical Manufacturers Association. Digital Imaging and
   Communications in Medicine (DICOM) Standard, Part 3: Information Object
   Definitions. PS3.3-2026c. Rosslyn, VA: NEMA; 2026.
   https://dicom.nema.org/medical/dicom/2026c/. Retrieved 2026-08-02. Read
   from the DocBook distribution pre-seeded on the measurement machine under
   PRE-04, `part03.xml`, 25,448,510 bytes, rather than over the network at run
   time.

9. National Electrical Manufacturers Association. Digital Imaging and
   Communications in Medicine (DICOM) Standard, Part 5: Data Structures and
   Encoding. PS3.5-2026c. Rosslyn, VA: NEMA; 2026.
   https://dicom.nema.org/medical/dicom/2026c/. Retrieved 2026-08-02. Section
   7.4.5 is the clause CP-2273 settles.

10. DICOM Correction Proposal CP-2273, Clarify whether zero length Type 3
    Sequences are allowed or not. Affects Part 5. Status: Standard, applied at
    edition 2026b. https://www.dclunie.com/dicom-status/status.html. Retrieved
    2026-08-03.

11. DICOM Supplement 243, Label Map Segmentation. DICOM Standards Committee,
    Working Group 6, work item 2023-10-B. Document status: Final Text,
    publication date 2024-09-14. In the standard: Standard, applied at edition
    2024c. https://www.dicomstandard.org/News-dir/ftsup/docs/sups/sup243.pdf.
    Retrieved 2026-08-03. sha256
    6b922b3bdee71a02a0de03dadebc647c848af2233c67f84f0772256f71d14e73.

12. DICOM Correction Proposal CP-2428, Add Algorithm Identification to RT Dose
    Module. Affects Parts 3, 6 and 16. Status: Standard, applied at edition
    2025c. https://www.dclunie.com/dicom-status/status.html. Retrieved
    2026-08-03.

13. DICOM Correction Proposal CP-2320, Communication that data is synthetic.
    Affects Part 3. Status: Standard, applied at edition 2024a.
    https://www.dclunie.com/dicom-status/status.html. Retrieved 2026-08-03.

14. DICOM Correction Proposal CP-1597, Clarify Segmentation Algorithm
    Parameters. Affects Part 3. Status: Standard, applied at edition 2016d.
    https://www.dclunie.com/dicom-status/status.html. Retrieved 2026-08-03.

15. DICOM Correction Proposal CP-1258, Refactor segment description, extend
    segment types and anatomy. Affects Parts 3 and 16. Status: Standard,
    applied at edition 2011. https://www.dclunie.com/dicom-status/status.html.
    Retrieved 2026-08-03.

16. DICOM Correction Proposal CP-2115, Per-segment multiple algorithms and
    creators. Affects Part 3. Status: Standard, applied at edition 2021d.
    https://www.dclunie.com/dicom-status/status.html. Retrieved 2026-08-03.

17. IHE International. IHE Radiology Technical Framework Supplement, AI
    Results (AIR). Rev. 1.3, Trial Implementation, 2025-08-08.
    https://www.ihe.net/uploadedFiles/Documents/Radiology/IHE_RAD_Suppl_AIR_Rev1-3_TI_2025-08-08.pdf.
    Retrieved 2026-08-02. sha256
    33C9E86326E8946BA2DB0B37E5FEE73A865C7B11A00201B983690FCA2ED1D964. Trial
    Implementation since 2020-07-16. The sha256 was re-verified against the
    pinned local copy 2026-08-03.

## Tools, each at the version that ran

18. Clunie DA. dicom3tools, `dciodvfy`, version package 1.00, snapshot
    20260701065818. https://www.dclunie.com/dicom3tools.html. Retrieved
    2026-08-03. The binary exposes no version flag and is pinned in
    `results/environment.json` by sha256 and mtime. The registered pin,
    snapshot 20240118131615, was never satisfied; see Methods 2.10.

19. OFFIS e.V. DCMTK: DICOM Toolkit, `dcmpschk`, `dcmdump`, `dcmp2pgm`,
    version 3.7.0, build 2025-12-15. https://dicom.offis.de/dcmtk. Retrieved
    2026-08-03.

20. pydicom project. dicom-validator, version 0.8.2.
    https://github.com/pydicom/dicom-validator. Retrieved 2026-08-03. Run
    against a pre-seeded standard path so that no measurement depends on a
    network fetch at run time.

21. Mason D. SU-E-T-33: Pydicom: An Open Source DICOM Library. Medical
    Physics. 2011;38(6Part10):3493. doi:10.1118/1.3611983. Version 3.0.2 as
    run, https://github.com/pydicom/pydicom.

22. Clunie DA. PixelMed Java DICOM Toolkit.
    https://www.pixelmed.com/dicomtoolkit.html. Retrieved 2026-08-03. The
    `DicomInstanceValidator` jar is absent from the pinned toolchain and did
    not run; see ledger row V-04.

23. Bridge CP, Gorman C, Pieper S, Doyle SW, Lennerz JK, Kalpathy-Cramer J, et
    al. Highdicom: a Python Library for Standardized Encoding of Image
    Annotations and Machine Learning Model Outputs in Pathology and Radiology.
    Journal of Digital Imaging. 2022;35(6):1719-1737.
    doi:10.1007/s10278-022-00683-y. Version 0.28.1 as installed; the
    registered pin was 0.28.0, see Methods 2.10.

24. Herz C, Fillion-Robin JC, Onken M, Riesmeier J, Lasso A, Pinter C, et al.
    dcmqi: An Open Source Library for Standardized Communication of
    Quantitative Image Analysis Results Using DICOM. Cancer Research.
    2017;77(21):e87-e90. doi:10.1158/0008-5472.CAN-17-0336.

25. Imaging Data Commons. idc-index, version 0.12.5, with idc-index-data
    24.2.2, carrying IDC release v24.
    https://github.com/ImagingDataCommons/idc-index. Retrieved 2026-08-03.

## Written from the producing side

26. Project MONAI. Contributing Equipment Sequence for DICOM SEG Writer.
    monai-deploy-app-sdk Discussion 528, opened 2025-02-20.
    https://github.com/Project-MONAI/monai-deploy-app-sdk/discussions/528.
    Retrieved 2026-08-03.

27. Murugesan GK, McCrumb D, Aboian M, Verma T, Soni R, Memon F, et al.
    AI-Generated Annotations Dataset for Diverse Cancer Radiology Collections
    in NCI Image Data Commons. Scientific Data. 2024;11(1):1165.
    doi:10.1038/s41597-024-03977-8.

28. Balliu M, Baudry B, Bobadilla S, Ekstedt M, Monperrus M, Ron J, et al.
    Challenges of Producing Software Bill of Materials for Java. IEEE Security
    &amp; Privacy. 2023;21(6):12-23. doi:10.1109/MSEC.2023.3302956.

29. Fedorov A, Clunie D, Ulrich E, Bauer C, Wahle A, Brown B, et al. DICOM for
    quantitative imaging biomarker development: a standards based approach to
    sharing clinical data and structured PET/CT analysis results in head and
    neck cancer research. PeerJ. 2016;4:e2057. doi:10.7717/peerj.2057.

## The three chains checked at primary source

30. Margolis D, Risher M, Ramakrishnan B, Brotman A, Jones J. SMTP MTA Strict
    Transport Security (MTA-STS). RFC 8461. IETF; 2018. doi:10.17487/RFC8461.

31. Moriarty K, Farrell S. Deprecating TLS 1.0 and TLS 1.1. RFC 8996, BCP 195.
    IETF; 2021. doi:10.17487/RFC8996.

32. Gillmor D. Negotiated finite field Diffie-Hellman ephemeral parameters for
    Transport Layer Security (TLS). RFC 7919. IETF; 2016.
    doi:10.17487/RFC7919.

33. Adrian D, Bhargavan K, Durumeric Z, Gaudry P, Green M, Halderman JA, et
    al. Imperfect Forward Secrecy: How Diffie-Hellman Fails in Practice. In:
    Proceedings of the 22nd ACM SIGSAC Conference on Computer and
    Communications Security. ACM; 2015:5-17. doi:10.1145/2810103.2813707.

## Prior work by this author

34. Patil D. Separating conformance from trustworthiness: an end-to-end audit,
    and five checks, for an AI result delivered into a clinical archive.
    Preprint and evaluation harness; 2026.
    https://github.com/Volkopat/spine-gsps. Retrieved 2026-08-03. Cited for
    its method. The released harness that accompanies it is the following
    entry and is the citable artefact; the title is as given in that harness's
    `CITATION.cff`.

35. Patil D. spine-gsps: evaluation harness for a deployed DICOM
    spine-labelling service, version v1.0.1. Zenodo; 2026-07-31.
    doi:10.5281/zenodo.21728679. https://github.com/Volkopat/spine-gsps.
    Version DOI 10.5281/zenodo.21728679, concept DOI 10.5281/zenodo.21728405.

36. Patil D. An on-premise, open-weights vision-language pipeline for
    burned-in PHI removal: detection, decision, and robustness on MIDI-B.
    Preprint and reproduction harness; 2026.
    https://github.com/Volkopat/palimpsest. Retrieved 2026-08-03. The
    reproduction harness that accompanies it is the following entry and is the
    citable artefact; the title is as given in that harness's README.

37. Patil D. palimpsest: reproduction harness for burned-in PHI removal on the
    MIDI-B benchmark, version 1.0.0. 2026-07-16.
    https://github.com/Volkopat/palimpsest. Retrieved 2026-08-03. No DOI has
    been minted for this harness at the time of writing.

## This study

38. Patil D. colophon: a conformance and provenance census of AI-derived DICOM
    objects in the NCI Imaging Data Commons, version 1.0.1. Zenodo.
    https://github.com/Volkopat/colophon. Version DOI `[FIELD: Zenodo version
    DOI, minted when the release is cut]`, concept DOI `[FIELD: Zenodo concept
    DOI]`.


## Removed from the text rather than left as a name

Nothing. Every surname that appeared in the drafted text resolved to a
published record. Two resolved to a different record than the drafting note
named, and both are recorded in the claims ledger rather than corrected
silently:

- The Gene Expression Omnibus metadata study was drafted as **Ochoa et al**. The
  DOI supplied, 10.1186/s13059-025-03725-0, resolves to Huang et al, and no
  author named Ochoa appears on it. The text now reads Huang et al (REF-02).
- The software bill-of-materials study was drafted as **IEEE S&P**, which reads
  as the Symposium. It appeared in the magazine, IEEE Security and Privacy
  21(6) (REF-03).
