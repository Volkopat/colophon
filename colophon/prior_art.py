"""The prior-art search, recorded so the negative result is auditable.

The brief requires a prior-art sweep before any code is written, and requires the
queries to go in the ledger. A claim of the form "nobody has published this" is
only checkable if the search that produced it is reproducible, so the queries are
data in this module rather than a remembered summary. spine-gsps had to soften a
literature claim for exactly this reason, after quoting a database count a
reviewer could not reproduce.

The sweep was run on 2026-08-01 as five independent searches, each on a different
angle, using general web search plus targeted retrieval of specific records. It
was carried out with LLM assistance, which is declared in `results/ai_use.md`.
Every hit below was retrieved and read. Items that could not be verified to a
venue are listed separately and are not cited.

Usage:
    python -m colophon.prior_art
"""
from __future__ import annotations

import sys

from . import ledger
from .paths import RESULTS

SEARCH_DATE = "2026-08-01"
CMD = "python -m colophon.prior_art"

# Verbatim query strings, one per line, exactly as issued.
QUERIES = [
    # angle 1: conformance audit of a public archive
    "DICOM conformance audit Imaging Data Commons",
    "Imaging Data Commons DICOM validation study",
    "TCIA DICOM conformance study dciodvfy validation failures public archive",
    "population scale DICOM validation public archive conformance rate",
    "DICOM segmentation object conformance errors highdicom dcmqi validator survey 2025",
    '"Imaging Data Commons" AI-derived DICOM SEG provenance metadata quality 2026',
    "MIDRC data quality DICOM metadata audit medical imaging data resource center",
    '"Toward AI-Ready Medical Imaging Data" arXiv 2025 DICOM conformance',
    "VIDS Verified Imaging Dataset Standard for Medical AI arXiv 2604.17525",
    "how many DICOM objects fail validator large repository fraction non-conformant measurement",
    "IDC Imaging Data Commons data curation quality control DICOM errors reported ingestion",
    "Fedorov Imaging Data Commons DICOM data quality validation errors paper 2025",
    "systematic assessment DICOM standard compliance research imaging repository census 2026",
    "DICOM4QI interoperability testing results segmentation structured report conformance QIICR",
    '"ContributingEquipmentSequence" OR "algorithm provenance" DICOM AI output audit archive study',
    "UK Biobank imaging DICOM conformance validation errors audit",
    "arXiv 2026 DICOM conformance census AI-derived objects public archive segmentation structured report",
    '"DICOM Header Mining and Metadata Quality Assurance" imaging data pipelines paper',
    "Posda TCIA curation validation error statistics DICOM collections percentage series",
    '"how conformant" OR "conformance rate" public DICOM datasets segmentation objects study measured',
    "DICOM conformance cardiac X-ray angiography ten vendors validation tools study conformant",
    "arxiv.org Imaging Data Commons conformance audit 2026 measurement study derived objects validators",
    "pubmed DICOM conformance validation Imaging Data Commons cancer archive 2025 2026",
    "TotalSegmentator DICOM SEG Imaging Data Commons conformance validation errors 14 TB collection",
    '"dcmpschk" OR "dciodvfy" large scale study thousands of DICOM files error rate reported',
    "measuring standards compliance machine learning outputs medical imaging repositories 2026 audit interoperability",
    "canceridc discourse dciodvfy validation errors DICOM SEG non-conformant IDC",
    'audit public medical imaging archive standard conformance 2026 "we validated" every object SOP class failure',
    "DICOM structured report TID1500 parametric map conformance errors public repository empirical study",
    # angle 2: validation of AI-derived objects
    "AI-derived DICOM object validation conformance study",
    "DICOM SEG conformance AI segmentation validation",
    "dcmqi validation study DICOM segmentation objects",
    "highdicom conformance evaluation library DICOM AI results",
    "IHE AI Results profile conformance measurement AIR profile DICOM",
    "Imaging Data Commons DICOM metadata quality audit conformance",
    "dciodvfy large-scale DICOM validation public dataset survey",
    "DICOM Structured Report TID1500 conformance validation study measurements",
    "2026 study conformance AI generated DICOM objects public archive population scale",
    "DICOM provenance AI algorithm ContributingEquipmentSequence missing attributes audit",
    "TotalSegmentator DICOM SEG Imaging Data Commons segmentations conformance",
    "DICOM Parametric Map Grayscale Softcopy Presentation State algorithm generated validation errors",
    "survey interoperability AI radiology vendor output DICOM non-conformant proprietary 2025",
    '"DICOM" segmentation objects "validation" errors rate encoders comparison study 2025 2026',
    "DICOM4QI connectathon interoperability testing results quantitative imaging objects findings",
    '"community-driven validation service" standard medical imaging objects Fedorov Clunie',
    "large-scale DICOM conformance error rate study thousands of studies validator PACS archive",
    "provenance metadata completeness AI model imaging derived objects study 2026 archive",
    "arxiv 2026 DICOM segmentation structured report validator dciodvfy dcmpschk dicom-validator study",
    "comparison DICOM SEG writers highdicom dcmqi pydicom-seg output validation differences",
    "FDA cleared AI imaging devices DICOM output standards conformance audit study",
    "Q-Bot automatic DICOM metadata monitoring quality management nuclear medicine SOP conformity",
    '"Imaging Data Commons" curation validation derived objects submitted analysis results quality checks paper',
    "systematic evaluation conformance derived DICOM objects TCIA public collections segmentation structured reports errors",
    'Krishnaswamy "Enrichment of the NLST and NSCLC-Radiomics" Scientific Data 2024',
    # angle 3: provenance and producer attribution
    "DICOM provenance ContributingEquipmentSequence AI algorithm identification",
    "AI model provenance DICOM metadata Manufacturer ManufacturerModelName attribution",
    "DICOM SEG segmentation objects conformance Imaging Data Commons validation study",
    '"AI-derived" DICOM objects provenance audit public archive metadata completeness',
    '"On the Encapsulation of Medical Imaging AI Algorithms" DICOM provenance',
    "model card DICOM imaging provenance AI transparency reporting standard 2025",
    "Imaging Data Commons DICOM metadata census analysis_result_id conformance survey 2026",
    "dciodvfy validation survey public DICOM archive TCIA non-conformance rates study",
    '"ContributingEquipmentSequence" AI segmentation highdicom provenance encoding practice',
    '"ImplementationVersionName" OR "(0002,0013)" DICOM producer identification study analysis',
    "large scale DICOM metadata quality analysis millions of instances attribute completeness archive",
    "traceability AI medical device output DICOM UDI device identification radiology regulatory audit trail",
    '"AlgorithmIdentificationSequence" missing DICOM SEG survey how often populated',
    "VIDS Verified Imaging Dataset Standard for Medical AI arXiv",
    "DICOM provenance Contributing Equipment AI",
    "Manufacturer attribute AI derived DICOM who produced segmentation unattributed",
    "Fedorov Clunie IDC DICOM conformance derived objects quality assessment 2025 2026",
    '"Imaging Data Commons" segmentation objects validator errors warnings how many fail dciodvfy',
    "algorithm identification DICOM SEG provenance empirical study derived objects repository",
    "DICOM Working Group 23 artificial intelligence provenance requirements attribution results objects",
    "census of AI-derived DICOM objects conformance provenance 2026 measurement study arXiv",
    '"Standardizing Medical Images at Scale for AI" arXiv 2603.15980 abstract',
    "de-identification removes Manufacturer ManufacturerModelName DICOM effect on provenance research archives",
    "TotalSegmentator DICOM SEG metadata model version recorded provenance IDC collection",
    "FAIR assessment imaging repository provenance metadata completeness AI outputs evaluation 2026",
    "TCIA analysis results collections derived DICOM provenance who created attribution measurement across collections",
    '"provenance" AND "DICOM" AND "artificial intelligence" 2026 paper measure how many objects identify producing software',
    # angle 4: validator disagreement
    "DICOM validator comparison dciodvfy dcmpschk agreement",
    "comparison of DICOM conformance validation tools DVTk dcm4che dciodvfy",
    "inter-validator agreement DICOM conformance measurement study",
    "Universidade de Aveiro DICOM validation service Costa Silva community-driven validation",
    '"dicom-validator" pydicom false positives comparison dciodvfy 2025',
    "DICOM segmentation object conformance validation Imaging Data Commons AI annotations 2025",
    '"validator" disagreement rate DICOM standard tools "false positive" benchmark study 2026',
    "benchmarking DICOM validation tools evaluation multiple validators discordance medical imaging informatics",
    "cardiac X-ray angiography DICOM conformance ten vendors two validation tools five visualization applications study",
    '"DICOM" conformance survey public archive TCIA "dciodvfy" errors warnings prevalence study',
    "assessment DICOM conformance angiographic images vendors validation tools interoperability journal",
    '"validators disagree" OR "disagreement between validators" DICOM conformance segmentation structured report',
    '"dcmpschk" DICOM validation tool dcmtk comparison evaluation',
    "arXiv 2026 DICOM conformance validation tools agreement study medical imaging archive audit",
    "Jorge Miguel Silva Carlos Costa DICOM validation tool 2021 2022 Dicoogle validation service evaluation",
    "Journal of Imaging Informatics in Medicine 2025 DICOM validation tools comparative evaluation conformance",
    "Posda validation rules dciodvfy comparison TCIA curation conformance errors quantified",
    'github pydicom dicom-validator issue "dciodvfy" different results comparison discrepancy',
    "highdicom generated DICOM objects fail dciodvfy warnings known good baseline validator noise",
    "DICOM structured report TID1500 validation PixelMed DICOMSRValidator versus dciodvfy disagreement conformance rates",
    "HL7 FHIR validator comparison disagreement between validators empirical study conformance tools",
    '"validator" agreement rate DICOM files flagged by one tool not another empirical measurement dicom3tools dcm4che',
    "arxiv 2026 DICOM segmentation structured report conformance census validators highdicom dcmqi measurement study",
    '"DICOM Validator Dashboard" 2024 2025 publication figure validation tool paper',
    "IHE Gazelle EVS DICOM object evaluation multiple validators dciodvfy results comparison",
    'Baljon Gerritsen Eichelberg Jensch "Quality Control using Automated Validation Tools" DICOM 1999',
    '"DICOM" conformance "two validators" OR "multiple validators" agreement kappa segmentation SR public dataset audit',
    # angle 5: GSPS literature and public GSPS data
    "DICOM Grayscale Softcopy Presentation State GSPS",
    '"Grayscale Softcopy Presentation State" paper 2025',
    "Eichelberg presentation state DICOM 2000 softcopy consistency paper",
    "Swinburne 2020 GSPS presentation state radiology annotations",
    "Harvey Corrie 2005 presentation state DICOM annotation PACS",
    '"presentation state" DICOM annotation interoperability 2024 2025 study',
    '"GSPS" DICOM public dataset download presentation state objects',
    'Church Warner Bradshaw "Opportunistic Promptable Segmentation" radiological annotations presentation state',
    'TCIA collection "Grayscale Softcopy Presentation State" series public archive',
    "public dataset DICOM presentation state objects released research corpus",
    'Imaging Data Commons "presentation state" GSPS collection IDC',
    '"presentation state" DICOM 2022 2023 journal article radiology informatics GSPS storage',
    "public GSPS dataset",
    "Grayscale Softcopy Presentation State dataset",
    "presentation state corpus DICOM public",
    'zenodo OR figshare OR kaggle DICOM "presentation state" PR modality sample files dataset',
    "DICOM conformance validation study public archive dciodvfy TCIA IDC non-conformant objects census",
    '"GSPS" annotations mining PACS radiologist measurements arrows 2025 deep learning dataset',
    "Riesmeier Eichelberg presentation state conformance test dcmtk evaluation implementations study",
    "highdicom DICOM presentation state python library encoding annotations paper",
    'IDC Imaging Data Commons collections "Grayscale Softcopy Presentation State Storage" SOP class instances count',
    'canceridc.dev OR imaging.datacommons.cancer.gov "PR" modality presentation state collection qin idc',
    '"presentation state" GSPS conformance audit 2026 measurement study DICOM objects archive',
    'arxiv 2026 "presentation state" DICOM validation conformance AI-derived objects Imaging Data Commons',
]

# Records retrieved directly rather than through a search result page.
RETRIEVED = [
    "https://arxiv.org/abs/2604.17525",
    "https://arxiv.org/abs/1806.08987",
    "https://ar5iv.labs.arxiv.org/html/1806.08987",
    "https://arxiv.org/abs/2306.00150",
    "https://arxiv.org/abs/2512.03541",
    "https://arxiv.org/abs/2602.00309",
    "https://learn.canceridc.dev/dicom/derived-objects",
    "PubMed records 37488323, 39438365, 35915366",
    'https://pubmed.ncbi.nlm.nih.gov/?term=%22presentation+state%22+DICOM (5 records)',
    'https://pubmed.ncbi.nlm.nih.gov/?term=%22softcopy+presentation+state%22 (1 record)',
    "https://pubmed.ncbi.nlm.nih.gov/?term=GSPS (312 records, acronym collision)",
    'Europe PMC REST, query "softcopy presentation state" (hitCount 17)',
    'Europe PMC REST, query "GSPS" AND "DICOM" (hitCount 28)',
    "https://api.openalex.org/works?search=DICOM%20validator%20comparison%20conformance",
]

FAILED_RETRIEVALS = [
    "https://arxiv.org/pdf/1806.08987, binary PDF not rendered",
    "Semantic Scholar graph API, HTTP 429 on every attempt, two tries per query",
]

# Nearest neighbours. Each was retrieved and read. `occupies` records whether a
# reviewer could say the census has already been done.
NEIGHBOURS = [
    {
        "title": "Reengineering Workflow for Curation of DICOM Datasets (Posda, TCIA)",
        "year": "2018",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6261183/",
        "occupies": "partial",
        "what": "Runs dciodvfy through RunDciodvfy.pl over whole TCIA collections, "
                "on the first file of every series, and clusters the errors.",
        "differs": "Publishes no rates, does not separate derived objects from "
                   "acquired ones, and does not examine provenance attributes. "
                   "It is the strongest existing precedent and the source of the "
                   "reviewer objection that IDC and TCIA already validate on "
                   "ingest. We cite it as the baseline and quantify the coverage "
                   "gap: per object rather than per series first file, with rates "
                   "and a floor.",
    },
    {
        "title": "Enrichment of lung cancer CT collections with AI-derived annotations "
                 "(Krishnaswamy et al.)",
        "year": "2024",
        "url": "https://www.nature.com/articles/s41597-023-02864-y",
        "occupies": "no",
        "what": "Producer-side self-validation of the authors' own SEG and TID1500 "
                "SR with dciodvfy and PixelMed DICOMSRValidator, as a release "
                "gate, reported in one Technical Validation sentence.",
        "differs": "No counts, no rates, no floor, no cross-tool comparison, and "
                   "only the authors' own objects. This is census subject, not "
                   "census.",
    },
    {
        "title": "AI-Generated Annotations Dataset for Diverse Cancer Radiology "
                 "Collections in NCI Imaging Data Commons (Murugesan et al.)",
        "year": "2024",
        "url": "https://www.nature.com/articles/s41597-024-03977-8",
        "occupies": "no",
        "what": "Releases AI-generated SEG across 11 IDC collections, validates its "
                "own new objects with dciodvfy, and sets SegmentAlgorithmType, "
                "SegmentAlgorithmName and ContentCreatorName.",
        "differs": "Reports no measurement of Manufacturer, ManufacturerModelName, "
                   "ImplementationVersionName or ContributingEquipmentSequence, and "
                   "does not examine objects it did not create. Its use of the SEG "
                   "algorithm attributes is why our carrier list is wider than the "
                   "brief's five.",
    },
    {
        "title": "VIDS: A Verified Imaging Dataset Standard for Medical AI (Muthu, Shalen)",
        "year": "2026",
        "url": "https://arxiv.org/abs/2604.17525",
        "occupies": "partial",
        "what": "A NIfTI-plus-sidecar dataset standard with 21 machine-enforceable "
                "rules, benchmarking four public datasets and reporting 20 to 39 "
                "percent satisfaction on provenance and quality documentation.",
        "differs": "Dataset packaging compliance against a standard its own authors "
                   "wrote, scored by its own validator, over four hand-picked "
                   "datasets. We measure DICOM IOD conformance of objects already "
                   "in a production archive, per object, with third party tools. "
                   "It must appear in related work: the general observation that "
                   "provenance is the largest documentation gap is no longer novel.",
    },
    {
        "title": "DICOM4QI demonstration and connectathon",
        "year": "2017 and ongoing",
        "url": "https://dicom4qi.readthedocs.io",
        "occupies": "partial",
        "what": "Multi-producer interoperability testing of SEG, TID1500 SR and "
                "Parametric Map across many platforms. Participants run both "
                "dciodvfy and PixelMed DicomSRValidator on the same objects and "
                "are asked to explain discrepancies.",
        "differs": "Hand-picked demonstration objects at an event, per-participant "
                   "pass and fail tables, no sampling frame, no agreement "
                   "statistic, and no peer-reviewed aggregate. It establishes that "
                   "validator disagreement is known, which is why claim 2 is "
                   "pitched as measurement rather than discovery.",
    },
    {
        "title": "DICOM image display consistency: a test environment "
                 "(Riesmeier, Eichelberg et al., SPIE 4323)",
        "year": "2001",
        "url": "https://www.spiedigitallibrary.org/conference-proceedings-of-spie/4323/",
        "occupies": "no",
        "what": "Builds a conformance test environment of test images and "
                "presentation states. Source of the DCMTK / MESA CPI suite, which "
                "is the only publicly downloadable GSPS data located.",
        "differs": "A synthetic conformance test set, not an archive census.",
    },
]

# Claims from the brief that the sweep changed. Recorded because an unrevised
# framing is how a paper acquires a defect it could have avoided.
CORRECTIONS = [
    {
        "id": "PA-C1",
        "was": "Nobody measures this.",
        "now": "Nobody publishes this.",
        "why": "Posda's RunDciodvfy.pl runs dciodvfy over TCIA collections. The "
               "original wording is falsifiable by a tool that exists. The "
               "published state of the art validates the first file of every "
               "series and reports no rates.",
    },
    {
        "id": "PA-C2",
        "was": "The IDC GSPS holdings are the only public GSPS corpus in existence.",
        "now": "No public corpus of clinical or archive-derived GSPS objects was "
               "located. The only public GSPS data found is a synthetic "
               "conformance test suite, DCMTK / MESA CPI.",
        "why": "The original is falsified by the MESA CPI suite. The corrected "
               "form survives and is the one that matters for a census.",
    },
    {
        "id": "PA-C3",
        "was": "The peer-reviewed GSPS literature is essentially Eichelberg 2000, "
               "Harvey and Corrie 2005, and Swinburne 2020.",
        "now": "Withdrawn as stated. It is wrong in both directions: it omits at "
               "least Church et al. 2026, Swinburne et al. 2025, Fischer et al. "
               "2015 and two Eichelberg-group SPIE papers, and Harvey and Corrie "
               "2005 is a NEMA conference paper hosted on dicom.nema.org, so it "
               "cannot sit inside a claim about peer-reviewed literature. If a "
               "sparsity claim is made it must quote database counts with the "
               "query strings and the date.",
        "why": "spine-gsps already had to soften a literature claim for quoting a "
               "count a reviewer could not reproduce. Same failure mode.",
    },
    {
        "id": "PA-C4",
        "was": "Claim 3 measures five provenance carriers.",
        "now": "Nine. The published IDC AI-annotation descriptors record producer "
               "information in SegmentAlgorithmName (0062,0009), "
               "SegmentAlgorithmType (0062,0008) and ContentCreatorName "
               "(0070,0084), and PS3.3 routes algorithm detail through the "
               "Algorithm Identification Macro and SR TID 4019.",
        "why": "Scoring only the brief's five would report an absence the objects "
               "may not have, which is a false negative we would have published.",
    },
    {
        "id": "PA-C5",
        "was": "Conformance is scored by dciodvfy, dcmpschk, dicom-validator and "
               "highdicom's reader.",
        "now": "Unchanged, but two limits are now stated rather than discovered "
               "later. dcmpschk validates presentation states only, so it has no "
               "role for SEG, SR, RTSTRUCT or Parametric Map. PixelMed "
               "DICOMSRValidator is in the IDC team's own SR pipeline and is not "
               "in the panel, so either it is added or its absence is stated in "
               "Methods.",
        "why": "A four-tool panel that is really a one-tool panel for most SOP "
               "classes is a Methods problem, not a result.",
    },
]

UNVERIFIED = [
    "A ten-vendor cardiac X-ray angiography conformance study, and a German "
    "Congress of Radiology 2006 CD test reportedly showing 80 percent failure. "
    "Both reach us only as second-hand quotations inside Silva et al. 2018.",
    "Baljon, Gerritsen, Eichelberg and Jensch 1999, recovered only from a "
    "reference list as \"Barcelona, p. 3, 1999\" with no proceedings name.",
    '"DICOM Header Mining and Metadata Quality Assurance", ResearchGate only, and '
    "its actual content is self-supervised representation learning from headers.",
    "Full author lists for the two SPIE presentation-state papers and the NEMA "
    "2005 authorship, because the PDFs could not be rendered.",
]

COVERAGE_LIMITS = (
    "All sweeps were English-language general web search plus targeted retrieval. "
    "Semantic Scholar returned HTTP 429 on every attempt. No systematic query was "
    "run against Google Scholar, Scopus, Web of Science, Embase or IEEE Xplore, "
    "and no search was made of the SPIE Medical Imaging, SIIM, EuroPACS, CARS or "
    "RSNA abstract archives. Those are the likeliest venues for an unindexed "
    "partial conformance sweep. One manual pass over them is scheduled before "
    "submission and will be logged here."
)


def write_markdown() -> str:
    rows = "\n".join(
        "| %s | %s | %s | %s | %s |"
        % (h["title"], h["year"], h["occupies"], h["what"], h["differs"])
        for h in NEIGHBOURS)
    corrections = "\n\n".join(
        "**%s.** Was: %s\n\nNow: %s\n\nWhy: %s"
        % (c["id"], c["was"], c["now"], c["why"]) for c in CORRECTIONS)
    queries = "\n".join("- `%s`" % q for q in QUERIES)
    retrieved = "\n".join("- %s" % r for r in RETRIEVED)
    failed = "\n".join("- %s" % r for r in FAILED_RETRIEVALS)
    unverified = "\n".join("- %s" % u for u in UNVERIFIED)

    text = f"""# Prior art, searched {SEARCH_DATE}

The brief requires this search before any code is written, and requires the
queries to be recorded so that the negative result is auditable. Reproduce the
record with `{CMD}`.

## Verdict

No publication was located that measures conformance or provenance completeness
of AI-derived DICOM objects across a population of producers in any public
archive, that quantifies inter-validator disagreement on a shared corpus, or
that measures producer-attribution attributes at population scale.

Every candidate resolves into one of four non-competing categories: validator
tool papers, curation-workflow papers that run validators operationally without
publishing rates, dataset descriptors that assert conformance without third-party
evidence, and guidance papers that recommend conformance checking.

## Nearest neighbours

| work | year | occupies the ground | what it does | how this study differs |
|---|---|---|---|---|
{rows}

## What this search changed

{corrections}

## Queries issued, verbatim

{len(QUERIES)} queries across five independent angles.

{queries}

## Records retrieved directly

{retrieved}

Retrievals that failed:

{failed}

## Items excluded for lack of a verifiable venue

Not cited anywhere in this project until resolved against a publisher record.

{unverified}

## Coverage limits of this search

{COVERAGE_LIMITS}
"""
    out = RESULTS / "prior_art.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return str(out)


def main(argv=None) -> int:
    path = write_markdown()
    print("wrote %s" % path)

    S = dict(section="PA", section_title="Prior art", command=CMD,
             source_file="results/prior_art.md", sop_class="all",
             validator="none, literature search",
             floor="not applicable, no validator involved",
             date_note="", verified_on=SEARCH_DATE)
    S.pop("date_note")

    partial = [h["title"] for h in NEIGHBOURS if h["occupies"] == "partial"]

    ledger.record_many([
        dict(id="PA-01", claim="No publication measures conformance or provenance "
             "of AI-derived DICOM objects across a population of producers in a "
             "public archive, quantifies inter-validator disagreement on a shared "
             "corpus, or measures producer attribution at population scale.",
             status="LITERATURE",
             value="%d queries across five angles, %d records retrieved directly, "
                   "0 works occupying the ground" % (len(QUERIES), len(RETRIEVED)),
             n="0", denominator=str(len(QUERIES)),
             status_note="This is a claim about our search, not about the "
             "literature. The queries are recorded verbatim in "
             "colophon/prior_art.py so a reviewer can re-run them. Searched with "
             "LLM assistance, declared in results/ai_use.md.",
             dropped=COVERAGE_LIMITS, **S),
        dict(id="PA-02", claim="Three works partially occupy adjacent ground and "
             "must be cited and distinguished rather than omitted.",
             status="LITERATURE",
             value="; ".join(partial), n=str(len(partial)),
             derived_from="PA-01", **S),
        dict(id="PA-03", claim="Validation of public DICOM archives is a "
             "documented, routine curation step. In every case the published "
             "record reports that validation was performed, not what it found.",
             status="LITERATURE",
             value="Posda operates a named workflow step, Verify DICOM IOD "
                   "(Dciodvfy); IDC declares use of dciodvfy and PixelMed "
                   "DICOMSRValidator; Krishnaswamy 2024 names both tools and "
                   "reports no numbers",
             external_source="https://pmc.ncbi.nlm.nih.gov/articles/PMC6261183/ "
                             "and https://www.nature.com/articles/s41597-023-02864-y",
             status_note="Contribution is scoped to published measurement: "
             "rates, denominators, per-error-class breakdown, warning classes "
             "and cross-validator disagreement. The word first is always "
             "qualified with that scope.",
             derived_from="PA-01", **S),
        dict(id="PA-03-prev", claim="The published state of the art in "
             "validating a public DICOM archive runs dciodvfy on the first file "
             "of every series.",
             status="RETIRED",
             value="withdrawn before submission",
             retired_reason="An overstatement that a reviewer catches by "
             "opening one file. It is true of RunDciodvfyByCollection.pl and of "
             "the 2018 paper, but Posda has a named workflow step supporting "
             "one_per_series, all_per_series and per_sop granularity. Replaced "
             "by PA-03, which claims only that the published record reports "
             "that validation happened rather than what it found.",
             superseded_by="PA-03", **S),
        dict(id="PA-08", claim="The genuinely uncovered ground is warnings. "
             "Existing collection-level tooling discards them by construction.",
             status="PENDING",
             value="RunDciodvfyByCollection.pl pipes dciodvfy output through "
                   "grep Error, discarding every warning, and additionally "
                   "suppresses (0018,9445)",
             status_note="Held PENDING until the source line is read directly. "
             "If confirmed, a warning-class breakdown is something no existing "
             "collection-level tooling can produce.",
             notes="Operational consequence, applied immediately: every dciodvfy "
                   "invocation in this project captures warnings as well as "
                   "errors. A harness that greps for Error inherits the blind "
                   "spot it exists to expose.",
             derived_from="PA-03", **S),
        dict(id="PA-09", claim="The denominators this study reports already "
             "exist inside every Posda instance and are never published.",
             status="PENDING",
             value="Posda parses dciodvfy output into structured error and "
                   "warning categories and stores num_file_in_unit, "
                   "num_errors_in_unit and num_warnings_in_unit in "
                   "dciodvfy_unit_scan",
             status_note="Held PENDING until the schema is read directly. This "
             "is the sharper and fairer version of the contribution claim: the "
             "measurement is not impossible or unattempted, it is unpublished.",
             derived_from="PA-03", **S),
        dict(id="PA-04", claim="No public corpus of clinical or archive-derived "
             "GSPS objects was located. The only public GSPS data found is a "
             "synthetic conformance test suite.",
             status="LITERATURE",
             value="DCMTK / MESA CPI presentation state test suite",
             status_note="Replaces the brief's stronger claim that the IDC GSPS "
             "holdings are the only public GSPS corpus in existence, which the "
             "MESA CPI suite falsifies. See PA-C2.",
             derived_from="PA-01,P0-05", **S),
        dict(id="PA-05", claim="The brief's characterisation of the peer-reviewed "
             "GSPS literature as essentially three papers does not survive and is "
             "withdrawn.",
             status="RETIRED",
             value="withdrawn before use",
             retired_reason="Wrong in both directions. It omits at least Church "
             "et al. 2026, Swinburne et al. 2025, Fischer et al. 2015 and two "
             "Eichelberg-group SPIE papers, and Harvey and Corrie 2005 is a NEMA "
             "conference paper, so it cannot sit inside a claim about "
             "peer-reviewed literature. Any sparsity claim must quote database "
             "counts with query strings and the date they were run.",
             notes="Never entered a manuscript. Recorded so it cannot be "
                   "reintroduced from the brief.", **S),
        dict(id="PA-06", claim="Claim 2 is a measurement of an acknowledged "
             "phenomenon, not a discovery. Validator authors concede disagreement "
             "in their own documentation.",
             status="LITERATURE",
             value="dciodvfy documentation concedes spurious diagnostics where "
                   "the standard is vague; the pydicom dicom-validator README "
                   "disclaims correctness and describes itself as beta-stage; "
                   "DICOM4QI instructs participants to explain discrepancies",
             status_note="Framing consequence: pitch claim 2 as supplying the "
             "rate, the direction and the per-attribute breakdown for something "
             "conceded qualitatively and never measured.",
             derived_from="PA-01", **S),
        dict(id="PA-07", claim="A manual pass over Google Scholar, Scopus, Web of "
             "Science, Embase, IEEE Xplore and the SPIE, SIIM, EuroPACS, CARS and "
             "RSNA abstract archives has not been run.",
             status="PENDING",
             value="0 of 10 additional venues searched",
             dropped="see coverage limits in results/prior_art.md",
             notes="Scheduled before submission. Logged now so the negative "
                   "result is not read as exhaustive.",
             **{k: v for k, v in S.items() if k != "dropped"}),
    ])
    print("ledger: %s" % ledger.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
