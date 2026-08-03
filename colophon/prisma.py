"""PRISMA-S style reporting of the prior-art search, so a negative claim is auditable.

A negative prior-art claim is worth exactly as much as the search behind it, and
"roughly 130 queries across five angles" is not a search a reviewer can check.
No database is named, no date range is given, no inclusion criterion is stated,
and no screened-versus-included counts exist. spine-gsps already had to soften a
literature claim for the same reason.

This module renders what `colophon.prior_art` actually recorded into the shape
PRISMA-S asks for, one row per source and per query, and it names every field
the record cannot fill. PRISMA-S is a reporting standard for search strategy in
systematic reviews. This was a web and API search, not a systematic review, so
the structure is borrowed and every departure is stated rather than papered
over.

Nothing here invents a hit count or a screening decision. A cell the record
cannot fill reads "not captured" and the gap list names it. The appendix is
generated rather than hand-maintained so the counts, the hit counts and the gap
list cannot drift out of agreement with the data in `colophon/prior_art.py`.

Ledger rows are proposed to `results/pending_ledger/track_g2.json` rather than
written straight into `results/ledger.csv`, because parallel tracks rewriting
the whole CSV would silently lose each other's rows. See
`colophon.merge_ledger`.

Usage:
    python -m colophon.prisma
"""
from __future__ import annotations

import ast
import csv
import io
import json
import re
import sys
import textwrap
import tokenize
import urllib.parse
from pathlib import Path

from . import ledger, prior_art
from .paths import RESULTS

CMD = "python -m colophon.prisma"
APPENDIX = RESULTS / "prisma_s_appendix.md"
ROWS_CSV = RESULTS / "prisma_s_rows.csv"
def _pending_path() -> Path:
    """Where this track's ledger proposal lives.

    A proposal sits in `results/pending_ledger/` until the orchestrator folds
    it into the ledger, after which it is archived under `merged/`. Pinning the
    first location alone means the module stops importing the moment the merge
    runs, which is a self-inflicted break rather than a real one.
    """
    base = RESULTS / "pending_ledger"
    for candidate in (base / "track_g2.json", base / "merged" / "track_g2.json"):
        if candidate.exists():
            return candidate
    return base / "track_g2.json"


PENDING = _pending_path()

NOT_CAPTURED = "not captured"
DIRECT = "not applicable, direct record retrieval"
FAILED = "0, retrieval failed"
NOT_SEARCHED_HITS = "not applicable, source not searched"

WEB_SOURCE = "general web search, engine not recorded"
WEB_INTERFACE = ("general web search issued from Claude Code; engine and "
                 "result-page interface not recorded")
RUN_BY = ("LLM assisted: Claude Code, Claude Opus 5 (1M context), Anthropic, "
          "supervised by the author. Declared in results/ai_use.md")

# The ten venues COVERAGE_LIMITS names as never searched. Held here as data so
# the not-searched rows are machine readable, and checked against the recorded
# text by tests/test_prisma.py so the two cannot drift apart.
NOT_SEARCHED = [
    "Google Scholar",
    "Scopus",
    "Web of Science",
    "Embase",
    "IEEE Xplore",
    "SPIE Medical Imaging",
    "SIIM",
    "EuroPACS",
    "CARS",
    "RSNA",
]

COLUMNS = [
    "row_type",
    "angle",
    "source",
    "interface",
    "date_searched",
    "query",
    "filters_limits",
    "hits_returned",
    "records_screened",
    "records_included",
    "exclusion_reason",
    "record",
    "run_by",
    "source_record",
    "notes",
]

COLUMN_MEANING = [
    ("row_type", "which part of the record the row came from: web_search_query, "
                 "targeted_retrieval, failed_retrieval, excluded_record, "
                 "included_record, source_not_searched"),
    ("angle", "which of the five independent sweeps the query belonged to, read "
              "from the section comments in colophon/prior_art.py"),
    ("source", "the database or source the query or retrieval was issued against"),
    ("interface", "how it was issued: a search box, a REST API, or a direct URL fetch"),
    ("date_searched", "the day the query was issued"),
    ("query", "the verbatim query string, or the decoded query parameter for a "
              "URL-encoded API call"),
    ("filters_limits", "any filter, limit or field restriction applied at the "
                       "interface, as distinct from operators inside the query string"),
    ("hits_returned", "the total number of records the source reported for the query"),
    ("records_screened", "how many of those records were examined"),
    ("records_included", "how many were carried forward into the prior-art record"),
    ("exclusion_reason", "why a screened record was not carried forward"),
    ("record", "the title or identifier of the record, for rows that are about a "
               "record rather than a query"),
    ("run_by", "who issued the query and with what assistance"),
    ("source_record", "the exact entry in colophon/prior_art.py this row was "
                      "generated from, so a reviewer can grep for it"),
    ("notes", "anything the record states that no other column carries"),
]

# PRISMA-S 2021 has 16 items. Each is answered from the record as it stands, not
# from what the search could have captured. The status vocabulary is deliberately
# narrow so the summary counts mean something, and comma free so the summary line
# is unambiguous.
PRISMA_STATUS = [
    ("reported", "the record answers the item"),
    ("partial", "the record answers part of it, and the missing part is named"),
    ("not done", "the method was not used, and the record says so rather than "
                 "leaving the item blank"),
    ("not captured", "the method may or may not have been used, and the record "
                     "cannot say"),
    ("not applicable", "the item does not arise for a search of this kind"),
]

PRISMA_S = [
    (1, "Database name", "partial",
     "Four named sources are recorded: PubMed, Europe PMC, OpenAlex and arXiv. "
     "The remaining web search rows were issued against a general web search "
     "whose engine is not recorded, so the source that produced most of this "
     "search cannot be named."),
    (2, "Multi-database searching", "partial",
     "Only a small minority of query rows were issued against a named database. "
     "No query string was translated into any database's own syntax; the same "
     "natural-language strings were used throughout. That is a departure from "
     "PRISMA-S item 2, which expects a strategy adapted per database."),
    (3, "Study registries", "not done",
     "No registry was searched. Registries index prospective clinical studies "
     "and none indexes imaging-informatics measurement studies, but no protocol "
     "registry and no preprint server were searched systematically either. arXiv "
     "records were retrieved individually, which is retrieval and not searching."),
    (4, "Online resources and browsing", "partial",
     "Documentation sites were read, including learn.canceridc.dev and "
     "dicom4qi.readthedocs.io. No site was searched through its own search box "
     "in any recorded way, and no browsing path is recorded."),
    (5, "Citation searching", "partial",
     "Backward citation chaining happened and left evidence: two items in the "
     "excluded register were reached only through the reference lists of other "
     "papers. It was ad hoc. No forward citation searching was run, and no "
     "systematic reference-list check of the included works is recorded."),
    (6, "Contacts", "not done",
     "No author, tool developer or archive maintainer was contacted."),
    (7, "Other methods", "reported",
     "The only other method used was targeted retrieval of specific records by "
     "URL or REST API. Every successful and every failed retrieval is recorded "
     "in colophon.prior_art RETRIEVED and FAILED_RETRIEVALS."),
    (8, "Full search strategies", "reported",
     "Every web search string is recorded verbatim in colophon.prior_art.QUERIES "
     "and rendered in results/prior_art.md and in results/prisma_s_rows.csv."),
    (9, "Limits and restrictions", "partial",
     "The record states the sweeps were English language. It does not record "
     "whether a language limit was set at the interface or whether English was "
     "simply the language of the queries and of the results read. No date limit "
     "was applied. Several strings contain a year as free text, which ranks "
     "results and does not restrict them."),
    (10, "Search filters", "not done",
     "No published search filter or methodological hedge was used. None exists "
     "for this topic."),
    (11, "Prior work", "not applicable",
     "No previously published search strategy was adapted or reused."),
    (12, "Updates", "reported",
     "No update has been run. Ledger row PA-07 carries the scheduled manual pass "
     "over the additional venues as PENDING, and this appendix carries those "
     "venues as source_not_searched rows."),
    (13, "Dates of searches", "reported",
     "Every query is dated %s, at day granularity. Per-query timestamps and the "
     "order in which the queries were issued are not recorded."
     % prior_art.SEARCH_DATE),
    (14, "Peer review", "not done",
     "No librarian or information specialist was involved at any point. The "
     "strategy was not peer reviewed, by PRESS or by anything else."),
    (15, "Total records", "not captured",
     "A handful of hit counts were captured. No total number of records "
     "identified exists and none can be reconstructed, because general web "
     "search results were read rather than exported."),
    (16, "Deduplication", "not captured",
     "No result set was exported, so no deduplication step was run and none can "
     "be described. Overlap between the five sweeps is unquantified."),
]

AUDITABILITY_RULE = (
    "A negative prior-art claim is auditable if and only if both of the "
    "following hold. (a) A third party can re-run every recorded query against "
    "the same source and reproduce the hit count within a stated tolerance. "
    "(b) Every record that was screened out has a recorded reason. A search "
    "that fails (a) can still be re-issued, but its verdict rests on the "
    "searcher's judgement rather than on evidence a reader can check. A search "
    "that fails (b) is a claim that nothing relevant was found, backed by no "
    "record of what was discarded."
)

# Gaps. kind is either a field the record cannot fill, or a limit on what the
# search covered. Both belong in the appendix; only the first kind is a
# reporting defect that better bookkeeping would have prevented.
FIELD_GAP = "field not captured"
COVERAGE_GAP = "coverage limit"

GAPS = [
    ("GAP-01", FIELD_GAP, "Search engine name",
     "The engine behind the general web search rows is not recorded. Without it "
     "the source cannot be named and no re-run is against the same source."),
    ("GAP-02", FIELD_GAP, "Hit counts",
     "Most query rows carry no hit count. Nothing was captured at search time, "
     "so nothing can be compared against a re-run."),
    ("GAP-03", FIELD_GAP, "Records screened",
     "How many results were examined per query, and in total, is not recorded."),
    ("GAP-04", FIELD_GAP, "Records included per query",
     "Inclusion is recorded at the level of the whole sweep, as the nearest "
     "neighbours list. Which query surfaced which included record is not "
     "recorded, so no query can be shown to have earned its place."),
    ("GAP-05", FIELD_GAP, "Exclusion reasons",
     "Only the items in the excluded register have a recorded reason. Every "
     "other record that was seen and passed over left no trace, so condition "
     "(b) of the auditability rule is unmet for them."),
    ("GAP-06", FIELD_GAP, "Filters and limits per query",
     "No filter, limit or field restriction is recorded as applied to any query. "
     "Whether that means none was applied cannot be established from the record."),
    ("GAP-07", FIELD_GAP, "Total records identified and deduplication",
     "No result set was exported, so there is no total, no overlap figure and no "
     "deduplication step to describe."),
    ("GAP-08", FIELD_GAP, "Screening depth",
     "How far down each result list was read is not recorded. A search that "
     "reads the first three results and one that reads the first fifty are "
     "indistinguishable in this record."),
    ("GAP-09", FIELD_GAP, "Inclusion and exclusion criteria set in advance",
     "None were written before the search. The four-category taxonomy in "
     "results/prior_art.md describes what was found and was formed after "
     "reading, which is not the same thing and is not presented as if it were."),
    ("GAP-10", FIELD_GAP, "Screeners and duplication",
     "One agent screened, once. There was no second screener, no duplicate "
     "screening and no reconciliation step, and no disagreement statistic exists."),
    ("GAP-11", FIELD_GAP, "Per-query timestamps and order",
     "Only the sweep date is recorded. The time of day and the order of issue "
     "are lost, so a re-run cannot reconstruct the state of any index at the "
     "moment a given query was answered."),
    ("GAP-12", FIELD_GAP, "Result snapshots",
     "No result page and no retrieved record was archived. The state of any "
     "source on the search date cannot be re-examined, and no archived snapshot "
     "exists to fall back on when a URL moves."),
    ("GAP-13", FIELD_GAP, "Semantic Scholar attempts",
     "The record states that Semantic Scholar returned HTTP 429 on every attempt "
     "with two tries per query. Which queries were tried is not recorded, so the "
     "failed arm of the search cannot be enumerated."),
    ("GAP-14", FIELD_GAP, "Retrieval log completeness",
     "Most of the included records have no entry in the recorded retrieval log, "
     "although the record states that each was retrieved and read. The retrieval "
     "log is therefore a partial log, and the count of direct retrievals is a "
     "floor rather than a total."),
    ("GAP-15", COVERAGE_GAP, "Venues never searched",
     "%d named venues were never searched. They are carried here as "
     % len(NOT_SEARCHED) +
     "source_not_searched rows and in ledger row PA-07."),
    ("GAP-16", COVERAGE_GAP, "Grey literature and code repositories",
     "Grey literature entered the record only where general web search happened "
     "to surface it. No repository, no issue tracker and no documentation site "
     "was searched systematically. Two pending claims rest on source code that "
     "was never retrieved, which is why they are PENDING."),
]


# --- reading the recorded data -----------------------------------------------

def _prior_art_source() -> str:
    return Path(prior_art.__file__).read_text(encoding="utf-8")


def query_angles() -> list[str]:
    """Which sweep each query belonged to.

    The angle labels live as section comments inside the QUERIES list rather
    than as data, so they are read from the source instead of retyped here.
    Retyping them is how a label stops matching the query it labels.
    """
    src = _prior_art_source()
    tree = ast.parse(src)
    node = None
    for stmt in tree.body:
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == "QUERIES"):
            node = stmt.value
    if node is None or not isinstance(node, (ast.List, ast.Tuple)):
        return [NOT_CAPTURED] * len(prior_art.QUERIES)

    labels: dict[int, str] = {}
    pattern = re.compile(r"#\s*angle\s*(\d+)\s*:\s*(.+)")
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type != tokenize.COMMENT:
            continue
        match = pattern.match(tok.string.strip())
        if match:
            labels[tok.start[0]] = "angle %s, %s" % (match.group(1),
                                                     match.group(2).strip())

    out = []
    for element in node.elts:
        current = NOT_CAPTURED
        for line in sorted(labels):
            if line <= element.lineno:
                current = labels[line]
        out.append(current)
    return out


_HIT_PATTERNS = (
    re.compile(r"\((\d+)\s+records?\b"),
    re.compile(r"hitCount\s+(\d+)"),
)


def captured_hits(record: str) -> str | None:
    """The hit count the record states, or None. Never a guess."""
    for pattern in _HIT_PATTERNS:
        match = pattern.search(record)
        if match:
            return match.group(1)
    return None


def _is_query_retrieval(record: str) -> bool:
    return ("?term=" in record or "?search=" in record
            or "query" in record.lower())


def classify_source(record: str) -> str:
    lowered = record.lower()
    if "ar5iv" in lowered:
        return "ar5iv, arXiv HTML mirror"
    if "arxiv.org" in lowered:
        return "arXiv"
    if "pubmed" in lowered:
        return "PubMed"
    if "europe pmc" in lowered:
        return "Europe PMC"
    if "openalex" in lowered:
        return "OpenAlex"
    if "semantic scholar" in lowered:
        return "Semantic Scholar"
    if "canceridc.dev" in lowered:
        return "learn.canceridc.dev, IDC documentation, grey literature"
    if "readthedocs" in lowered:
        return "readthedocs, grey literature"
    if "nature.com" in lowered:
        return "nature.com, publisher site"
    if "pmc.ncbi.nlm.nih.gov" in lowered:
        return "PubMed Central"
    if "spiedigitallibrary" in lowered:
        return "SPIE Digital Library, publisher site"
    return NOT_CAPTURED


def classify_interface(record: str) -> str:
    lowered = record.lower()
    if "rest" in lowered:
        return "REST API over HTTP, issued from Claude Code"
    if record.startswith("http"):
        return "direct HTTP retrieval of the recorded URL, issued from Claude Code"
    if lowered.startswith("pubmed records"):
        return "PubMed record retrieval by PMID, issued from Claude Code"
    if re.search(r"\bapi\b", lowered):
        return "HTTP API, issued from Claude Code"
    return NOT_CAPTURED


def extract_query(record: str) -> str:
    """The query string a retrieval record carries, decoded where URL encoded.

    Decoding is a transformation of the recorded string, not an addition to it:
    the encoded form is kept in source_record so both are on the page.
    """
    if "?" in record and record.startswith("http"):
        url = record.split()[0]
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        for key in ("term", "search", "q", "query"):
            if key in params:
                return params[key][0]
    match = re.search(r"query\s+(.+?)\s*\(", record)
    if match:
        return match.group(1).strip()
    return NOT_CAPTURED


def _blank_row() -> dict:
    return {c: "" for c in COLUMNS}


# --- executed database and documentary searches -------------------------------
# Everything above this point describes a search that was LLM assisted and whose
# interface was not captured, which is why so many cells read "not captured".
# These five were executed directly against a public API and a public document,
# with the exact query, the interface and the integer returned, so every cell is
# filled. They are the auditable part of this appendix.
EPMC_INTERFACE = ("Europe PMC REST API, "
                  "https://www.ebi.ac.uk/europepmc/webservices/rest/search")
EXECUTED_SEARCHES = [
    {"row_type": "database_query",
     "angle": "angle 5, the attribute names themselves",
     "source": "Europe PMC", "interface": EPMC_INTERFACE,
     "date_searched": "2026-08-02",
     "query": "SegmentationAlgorithmIdentificationSequence OR "
              "ContributingEquipmentSequence OR SegmentAlgorithmName",
     "filters_limits": "none, all indexed literature, format=json",
     "hits_returned": "2", "records_screened": "2", "records_included": "2",
     "exclusion_reason": "none excluded, both hits identified and reported",
     "record": "PMID 41113334 doi 10.1016/j.csbj.2025.09.041; "
               "PMID 39443503 doi 10.1038/s41597-024-03977-8",
     "source_record": "ledger PA-10",
     "notes": "Recorded as not executed in COLOPHON_ADDENDUM_03 section 5 item "
              "3. Executed here. Neither hit reports a population or a rate "
              "over these attributes."},
    {"row_type": "database_query",
     "angle": "angle 5, the attribute names themselves",
     "source": "Europe PMC", "interface": EPMC_INTERFACE,
     "date_searched": "2026-08-02",
     "query": "SegmentationAlgorithmIdentificationSequence",
     "filters_limits": "none", "hits_returned": "0", "records_screened": "0",
     "records_included": "0",
     "exclusion_reason": "not applicable, zero hits", "record": "none",
     "source_record": "ledger PA-10",
     "notes": "The attribute name does not appear anywhere in the corpus."},
    {"row_type": "database_query",
     "angle": "angle 5, the attribute names themselves",
     "source": "Europe PMC", "interface": EPMC_INTERFACE,
     "date_searched": "2026-08-02", "query": "ContributingEquipmentSequence",
     "filters_limits": "none", "hits_returned": "0", "records_screened": "0",
     "records_included": "0",
     "exclusion_reason": "not applicable, zero hits", "record": "none",
     "source_record": "ledger PA-10",
     "notes": "The attribute name does not appear anywhere in the corpus."},
    {"row_type": "database_query",
     "angle": "angle 5, the attribute names themselves",
     "source": "Europe PMC", "interface": EPMC_INTERFACE,
     "date_searched": "2026-08-02",
     "query": "(SegmentationAlgorithmIdentificationSequence OR "
              "ContributingEquipmentSequence OR SegmentAlgorithmName) AND "
              "(population OR rate OR census OR audit)",
     "filters_limits": "none", "hits_returned": "2", "records_screened": "2",
     "records_included": "0",
     "exclusion_reason": "neither hit reports a population or a rate over the "
                         "attributes",
     "record": "the same two records as the union query",
     "source_record": "ledger PA-10",
     "notes": "Per-term crossed counts: population 1, rate 2, census 0, audit 0."},
    {"row_type": "documentary_search",
     "angle": "angle 6, has the change already been proposed",
     "source": "DICOM Correction Proposals by Number",
     "interface": "https://www.dclunie.com/dicom-status/status.html",
     "date_searched": "2026-08-02",
     "query": "complete numbered CP series, title screening on segmentation, "
              "algorithm, provenance, equipment",
     "filters_limits": "titles only, CP bodies not read",
     "hits_returned": "2,648", "records_screened": "78", "records_included": "0",
     "exclusion_reason": "no CP promotes a provenance attribute from Type 3 to "
                         "conditional",
     "record": "nearest prior actions leaving the Type unchanged: CP-1597, "
               "CP-1258, CP-2115; counter-current confirmed: CP-2428, CP-2320",
     "source_record": "ledger PA-11",
     "notes": "COLOPHON_ADDENDUM_03 section 4 recorded this negative as "
              "UNVERIFIED before 2023 because the table truncated in fetch. The "
              "full series CP-1 to CP-2649 parses here, so the negative no "
              "longer needs a window."},
]


def build_rows() -> list[dict]:
    """Every row of the appendix table, in the order the record holds them."""
    rows: list[dict] = []
    angles = query_angles()
    retrieved_blob = "\n".join(prior_art.RETRIEVED)

    for i, query in enumerate(prior_art.QUERIES):
        row = _blank_row()
        row.update({
            "row_type": "web_search_query",
            "angle": angles[i] if i < len(angles) else NOT_CAPTURED,
            "source": WEB_SOURCE,
            "interface": WEB_INTERFACE,
            "date_searched": prior_art.SEARCH_DATE,
            "query": query,
            "filters_limits": NOT_CAPTURED,
            "hits_returned": NOT_CAPTURED,
            "records_screened": NOT_CAPTURED,
            "records_included": NOT_CAPTURED,
            "exclusion_reason": NOT_CAPTURED,
            "record": "not applicable, this row is a query",
            "run_by": RUN_BY,
            "source_record": "colophon.prior_art.QUERIES[%d]" % i,
            "notes": "",
        })
        rows.append(row)

    for i, record in enumerate(prior_art.RETRIEVED):
        hits = captured_hits(record)
        is_query = _is_query_retrieval(record)
        note = ""
        parenthetical = re.search(r"\(([^)]*)\)", record)
        if parenthetical:
            note = "recorded parenthetical: %s" % parenthetical.group(1)
        row = _blank_row()
        row.update({
            "row_type": "targeted_retrieval",
            "angle": NOT_CAPTURED,
            "source": classify_source(record),
            "interface": classify_interface(record),
            "date_searched": prior_art.SEARCH_DATE,
            "query": extract_query(record) if is_query else
                     "not applicable, record retrieved by identifier or URL",
            "filters_limits": NOT_CAPTURED,
            "hits_returned": hits if hits is not None else
                             (NOT_CAPTURED if is_query else DIRECT),
            "records_screened": NOT_CAPTURED,
            "records_included": NOT_CAPTURED,
            "exclusion_reason": NOT_CAPTURED,
            "record": record.split()[0] if record.startswith("http") else record,
            "run_by": RUN_BY,
            "source_record": "colophon.prior_art.RETRIEVED[%d]: %s" % (i, record),
            "notes": note,
        })
        rows.append(row)

    for i, record in enumerate(prior_art.FAILED_RETRIEVALS):
        head, _, reason = record.partition(",")
        row = _blank_row()
        row.update({
            "row_type": "failed_retrieval",
            "angle": NOT_CAPTURED,
            "source": classify_source(record),
            "interface": classify_interface(head.strip()),
            "date_searched": prior_art.SEARCH_DATE,
            "query": head.strip() if head.startswith("http") else NOT_CAPTURED,
            "filters_limits": NOT_CAPTURED,
            "hits_returned": FAILED,
            "records_screened": "0",
            "records_included": "0",
            "exclusion_reason": reason.strip() or NOT_CAPTURED,
            "record": head.strip(),
            "run_by": RUN_BY,
            "source_record": "colophon.prior_art.FAILED_RETRIEVALS[%d]: %s" % (i, record),
            "notes": "the retrieval failed, so no record reached screening",
        })
        rows.append(row)

    for i, item in enumerate(prior_art.UNVERIFIED):
        row = _blank_row()
        row.update({
            "row_type": "excluded_record",
            "angle": NOT_CAPTURED,
            "source": NOT_CAPTURED,
            "interface": NOT_CAPTURED,
            "date_searched": prior_art.SEARCH_DATE,
            "query": "not captured, the query that surfaced this record is not recorded",
            "filters_limits": "not applicable",
            "hits_returned": "not applicable",
            "records_screened": "1",
            "records_included": "0",
            "exclusion_reason": "no verifiable venue located. Not cited anywhere "
                                "in this project until resolved against a "
                                "publisher record",
            "record": item,
            "run_by": RUN_BY,
            "source_record": "colophon.prior_art.UNVERIFIED[%d]" % i,
            "notes": "the recorded detail of why the venue could not be verified "
                     "is in the record column, verbatim",
        })
        rows.append(row)

    for i, neighbour in enumerate(prior_art.NEIGHBOURS):
        url = neighbour["url"]
        logged = url in retrieved_blob
        row = _blank_row()
        row.update({
            "row_type": "included_record",
            "angle": NOT_CAPTURED,
            "source": classify_source(url),
            "interface": NOT_CAPTURED,
            "date_searched": prior_art.SEARCH_DATE,
            "query": "not captured, the query that surfaced this record is not recorded",
            "filters_limits": "not applicable",
            "hits_returned": "not applicable",
            "records_screened": "1",
            "records_included": "1",
            "exclusion_reason": "not applicable, this record was included",
            "record": "%s (%s), %s" % (neighbour["title"], neighbour["year"], url),
            "run_by": RUN_BY,
            "source_record": "colophon.prior_art.NEIGHBOURS[%d]" % i,
            "notes": ("occupies the ground: %s. " % neighbour["occupies"])
                     + ("URL present in the recorded retrieval log" if logged else
                        "URL absent from the recorded retrieval log, see GAP-14"),
        })
        rows.append(row)

    for venue in NOT_SEARCHED:
        row = _blank_row()
        row.update({
            "row_type": "source_not_searched",
            "angle": "not applicable",
            "source": venue,
            "interface": "not searched",
            "date_searched": "not searched",
            "query": "not applicable, no query was issued against this source",
            "filters_limits": "not applicable",
            "hits_returned": NOT_SEARCHED_HITS,
            "records_screened": "0",
            "records_included": "0",
            "exclusion_reason": "not applicable, the source was never searched",
            "record": "not applicable",
            "run_by": "not applicable",
            "source_record": "colophon.prior_art.COVERAGE_LIMITS",
            "notes": "named as not searched in COVERAGE_LIMITS and in ledger row PA-07",
        })
        rows.append(row)

    for entry in EXECUTED_SEARCHES:
        row = _blank_row()
        row.update(entry)
        # These were run directly by the author against a public interface, so
        # the LLM-assistance declaration that every other row carries does not
        # apply and saying otherwise would misdeclare them.
        row["run_by"] = ("author, executed directly against the public "
                         "interface named in this row")
        rows.append(row)
    return rows


# --- counting ----------------------------------------------------------------

def is_numeric(value: str) -> bool:
    return bool(re.fullmatch(r"\d+", value.strip()))


def counts(rows: list[dict]) -> dict:
    """Every number the appendix states, computed once from the rows."""
    by_type: dict[str, int] = {}
    for row in rows:
        by_type[row["row_type"]] = by_type.get(row["row_type"], 0) + 1

    query_rows = [r for r in rows
                  if r["row_type"] in ("web_search_query", "targeted_retrieval")
                  and r["hits_returned"] != DIRECT]
    with_hits = [r for r in query_rows if is_numeric(r["hits_returned"])]

    prisma_status: dict[str, int] = {}
    for _, _, status, _ in PRISMA_S:
        prisma_status[status] = prisma_status.get(status, 0) + 1

    included = [r for r in rows if r["row_type"] == "included_record"]
    unlogged = [r for r in included if "absent from the recorded" in r["notes"]]

    named_sources = sorted({r["source"] for r in rows
                            if r["row_type"] == "targeted_retrieval"
                            and r["source"] != NOT_CAPTURED})
    failed_sources = sorted({r["source"] for r in rows
                             if r["row_type"] == "failed_retrieval"
                             and r["source"] != NOT_CAPTURED})

    return {
        "rows": len(rows),
        "by_type": by_type,
        "query_rows": len(query_rows),
        "hits_captured": len(with_hits),
        "hits_not_captured": len(query_rows) - len(with_hits),
        "web_query_rows": by_type.get("web_search_query", 0),
        "prisma_status": prisma_status,
        "prisma_items": len(PRISMA_S),
        "field_gaps": sum(1 for g in GAPS if g[1] == FIELD_GAP),
        "coverage_gaps": sum(1 for g in GAPS if g[1] == COVERAGE_GAP),
        "included": len(included),
        "included_unlogged": len(unlogged),
        "not_searched": len(NOT_SEARCHED),
        "named_sources": named_sources,
        "failed_sources": failed_sources,
    }


# --- rendering ----------------------------------------------------------------

def _cell(value: str) -> str:
    return str(value).replace("|", "\\|")


def _rewrap(text: str, width: int = 79) -> str:
    """Reflow the prose paragraphs only.

    Numbers are interpolated into the prose, so a paragraph written at a fixed
    width in the template comes out ragged once the numbers change length. Tables
    and fenced or indented blocks are left alone: rewrapping a table row destroys
    it.
    """
    def fill(body, **kw):
        # A broken hyphenated word and a split URL are both worse than a long
        # line, so neither is allowed.
        return textwrap.fill(body, width=width, break_on_hyphens=False,
                             break_long_words=False, **kw)

    blocks = []
    for block in text.split("\n\n"):
        lines = [line for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        if any(line.startswith(("|", "#", "    ", "\t", "```")) for line in lines):
            blocks.append(block.strip("\n"))
        elif lines[0].startswith("> "):
            body = " ".join(line.lstrip("> ").strip() for line in lines)
            blocks.append(fill(body, initial_indent="> ", subsequent_indent="> "))
        elif lines[0].startswith("- "):
            items, current = [], ""
            for line in lines:
                if line.startswith("- "):
                    if current:
                        items.append(current)
                    current = line[2:].strip()
                else:
                    current += " " + line.strip()
            if current:
                items.append(current)
            blocks.append("\n".join(
                fill(item, initial_indent="- ", subsequent_indent="  ")
                for item in items))
        else:
            blocks.append(fill(" ".join(line.strip() for line in lines)))
    return "\n\n".join(blocks) + "\n"


def write_csv(rows: list[dict], path: Path = ROWS_CSV) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in COLUMNS})
    return str(path)


def render_markdown(rows: list[dict]) -> str:
    c = counts(rows)

    schema = "\n".join("| `%s` | %s |" % (name, meaning)
                       for name, meaning in COLUMN_MEANING)

    row_counts = "\n".join(
        "| `%s` | %d |" % (kind, c["by_type"].get(kind, 0))
        for kind in ("web_search_query", "targeted_retrieval", "failed_retrieval",
                     "excluded_record", "included_record", "source_not_searched"))

    prisma = "\n".join(
        "| %d | %s | %s | %s |" % (n, title, status, _cell(text))
        for n, title, status, text in PRISMA_S)
    prisma_summary = "; ".join(
        "%s %d" % (status, c["prisma_status"].get(status, 0))
        for status, _ in PRISMA_STATUS)
    prisma_legend = "\n".join("| %s | %d | %s |" % (
        status, c["prisma_status"].get(status, 0), meaning)
        for status, meaning in PRISMA_STATUS)

    named = [r for r in rows if r["row_type"] in ("targeted_retrieval",
                                                  "failed_retrieval")]
    named_table = "\n".join(
        "| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            _cell(r["source"]), _cell(r["interface"]), r["date_searched"],
            _cell(r["query"]), _cell(r["record"]), _cell(r["hits_returned"]),
            _cell(r["records_screened"]), _cell(r["records_included"]),
            _cell(r["exclusion_reason"]))
        for r in named)

    web = [r for r in rows if r["row_type"] == "web_search_query"]
    web_table = "\n".join(
        "| %d | %s | `%s` |" % (i + 1, _cell(r["angle"]), _cell(r["query"]))
        for i, r in enumerate(web))

    excluded = [r for r in rows if r["row_type"] == "excluded_record"]
    excluded_table = "\n".join(
        "| %s | %s | %s | %s |" % (_cell(r["record"]), r["records_screened"],
                                   r["records_included"],
                                   _cell(r["exclusion_reason"]))
        for r in excluded)

    included = [r for r in rows if r["row_type"] == "included_record"]
    included_table = "\n".join(
        "| %s | %s | %s |" % (_cell(r["record"]), _cell(r["source"]),
                              _cell(r["notes"]))
        for r in included)

    not_searched_table = "\n".join(
        "| %s | %s | %s |" % (_cell(r["source"]), r["records_screened"],
                              _cell(r["notes"]))
        for r in rows if r["row_type"] == "source_not_searched")

    field_gaps = "\n".join(
        "| %s | %s | %s |" % (gid, title, _cell(text))
        for gid, kind, title, text in GAPS if kind == FIELD_GAP)
    coverage_gaps = "\n".join(
        "| %s | %s | %s |" % (gid, title, _cell(text))
        for gid, kind, title, text in GAPS if kind == COVERAGE_GAP)

    return _rewrap(f"""# Appendix S. Search strategy for the prior-art claim

Generated by `{CMD}` from the data in `colophon/prior_art.py`. The
machine-readable table is `results/prisma_s_rows.csv`, one row per source and
per query. The prior-art verdict this appendix supports is
`results/prior_art.md`, ledger row PA-01.

## S.1 What this appendix is, and what it is not

PRISMA-S is the reporting extension that says how a systematic review's search
should be described. This was not a systematic review. It was a web and API
search run in one day by one agent, with no protocol, no librarian, no second
screener and no exported result sets.

The structure is borrowed because it is the right structure for making a
negative claim checkable, and because a reviewer who knows PRISMA-S can see at a
glance what is missing. Section S.7 answers all {c["prisma_items"]} PRISMA-S
items from the record as it stands, including the items whose honest answer is
that the method was not used or that nothing was captured. Nothing in this
appendix should be read as a claim that a systematic review was conducted.

## S.2 The auditability rule

Stated as a rule, so it can be applied to this search and fail.

> {AUDITABILITY_RULE}

Applied to this search:

- Condition (a) is met for {c["hits_captured"]} of {c["query_rows"]} query rows.
  It fails for the other {c["hits_not_captured"]}, which carry no hit count at
  all.
- Condition (b) is met only for the {c["by_type"].get("excluded_record", 0)}
  records in the excluded register. Every other record that was read and passed
  over left no trace, so its exclusion has no recorded reason.

The honest consequence: the negative claim is auditable in the weak sense that
every query can be re-issued and the verdict re-tested by a third party, and it
is not auditable in the strong sense that its counts can be reproduced. It is
reported that way rather than dressed up.

## S.3 Tolerance

A tolerance is only meaningful per source class, because the sources differ in
whether they have a reproducible notion of a hit count at all.

| source class | tolerance for a re-run | rationale |
|---|---|---|
| Named bibliographic database with a stable query interface: PubMed, Europe PMC, OpenAlex | the re-run count is within 5 percent of the recorded count, or the excess is accounted for by records whose entry date is later than {prior_art.SEARCH_DATE} | these indexes grow monotonically and answer the same query string deterministically on a given day, so a re-run count below the recorded count indicates a mis-transcribed query rather than index drift, and has to be explained |
| Documentation sites, code repositories, publisher record pages | no count applies; the audit is binary, the named artefact is present at the recorded URL or it is not | these are single records, not result sets. Where a URL has moved, an archived snapshot is the fallback, and this search archived none, which is GAP-12 |
| General web search | none can be stated | the engine is not recorded, results are ranked, personalised, regionalised and continuously re-indexed, and no count was captured. At no tolerance can condition (a) be met for these rows |

That last row is the load-bearing limitation of this search: hit counts from
general web search are not reproducible in the way a database query is, and
{c["web_query_rows"]} of {c["query_rows"]} query rows are general web search.
The right response is not to quote a web hit count with a wide tolerance. It is
to state that no count exists and to carry the queries themselves as the
reproducible artefact.

## S.4 Schema

One row per source and per query, plus rows for the records that were screened
out, the records that were included, and the sources that were never searched.
`row_type` says which.

| column | meaning |
|---|---|
{schema}

Every cell the record cannot fill reads "not captured". No hit count and no
screening decision in this appendix was reconstructed, inferred or estimated.

## S.5 Row counts

| row type | rows |
|---|---|
{row_counts}
| **total** | **{c["rows"]}** |

Of the {c["query_rows"]} rows that represent a query against a source,
{c["hits_captured"]} carry a hit count captured at search time and
{c["hits_not_captured"]} do not. Rows that retrieved a single known record by
URL or identifier are excluded from that denominator, because a hit count does
not arise for them.

## S.6 Narrative fields

**Information sources searched.** One general web search of unrecorded engine,
which produced {c["web_query_rows"]} of the query rows, plus these named sources
reached by URL or API: {"; ".join(c["named_sources"])}.

**Retrievals that failed.** {c["by_type"].get("failed_retrieval", 0)} recorded,
listed with their reasons in section S.8. The sources involved:
{"; ".join(c["failed_sources"])}. Semantic Scholar returned HTTP 429 on every
attempt and contributed nothing to this search. Which queries were tried against
it is not recorded, which is GAP-13.

**Information sources not searched.** {c["not_searched"]} named venues, listed
in section S.12 and in ledger row PA-07. They are the likeliest venues for an
unindexed partial conformance sweep, which is why the negative claim is reported
with them named rather than with the search described as exhaustive.

**Grey literature.** Included, but not systematically. Grey literature entered
this record only where general web search happened to surface it, and it matters
here more than it would in a clinical review: the closest prior work, the Posda
curation tooling used by TCIA, is a 2018 journal article plus a code repository,
and the parts of it this project relies on are the code and the database schema
rather than the article. Two ledger rows, PA-08 and PA-09, are held PENDING
precisely because that source was never retrieved and read directly. No
repository host, no issue tracker and no documentation site was searched through
its own search interface in any recorded way. See GAP-16.

**Citation chaining.** Backward chaining was used, ad hoc, and left evidence in
the excluded register: two items are recorded as reaching this search only
through the reference lists of other papers. No forward citation searching was
run. No systematic reference-list check of the {c["included"]} included records
is recorded. See GAP-05 and section S.11.

**Librarian.** None. No librarian or information specialist was involved at any
stage of designing, running or checking this search.

**Peer review of the search.** None. The strategy was not reviewed by PRESS or
by any other means before or after it was run.

**Date limits.** None applied. Some query strings contain a year as free text,
which influences ranking and does not restrict the result set. All queries were
issued on {prior_art.SEARCH_DATE}.

**Language limits.** English only. The record states the sweeps were English
language. Whether a language limit was set at the interface, or English was
simply the language of the queries and of the results read, is not captured.
No non-English source was searched and no translation was used.

**Who ran it, and how.** {RUN_BY}. The queries were composed and issued by the
LLM agent under the author's direction, the results were read by the agent, and
the record in `colophon/prior_art.py` is the agent's log of what it issued and
what it retrieved. The author is responsible for every claim drawn from it. This
matters for reading the gap list: the gaps are what a one-pass agentic search
does not capture unless it is instrumented to, and it was not.

## S.7 PRISMA-S, item by item

Across the {c["prisma_items"]} items: {prisma_summary}.

| status | items | meaning |
|---|---|---|
{prisma_legend}

| # | PRISMA-S item | status | how this search answers it |
|---|---|---|---|
{prisma}

## S.8 Named sources, one row per query or retrieval

Filters or limits: "not captured" on every row. Run by: as section S.6. Both
columns are omitted here and carried in full in `results/prisma_s_rows.csv`.

| source | interface | date searched | query | record | hits returned | records screened | records included | reason for exclusion |
|---|---|---|---|---|---|---|---|---|
{named_table}

## S.9 General web search, one row per search string

Constant across every row in this table, and carried per row in the CSV: source
"{WEB_SOURCE}", interface "{WEB_INTERFACE}", date searched
{prior_art.SEARCH_DATE}, filters or limits "not captured", hits returned "not
captured", records screened "not captured", records included "not captured",
reason for exclusion "not captured".

Quotation marks, `OR` and `AND` inside a string are operators the searcher typed
into the query, not filters applied at an interface.

| # | angle | verbatim query string |
|---|---|---|
{web_table}

## S.10 Records screened out, with the recorded reason

The only records whose exclusion has a recorded reason. Everything else read
during the sweep and passed over is unrecorded, which is GAP-05. The record
column is the verbatim entry, because the recorded detail of why each venue
could not be verified is part of the record's own wording and is not restated.

| record | screened | included | reason for exclusion |
|---|---|---|---|
{excluded_table}

## S.11 Records included

| record | source | note |
|---|---|---|
{included_table}

{c["included_unlogged"]} of {c["included"]} included records have no entry in
the recorded retrieval log, although the record states each was retrieved and
read. The retrieval log is therefore partial, and the count of direct
retrievals is a floor rather than a total. See GAP-14.

## S.12 Sources not searched

| source | records screened | note |
|---|---|---|
{not_searched_table}

## S.13 Gap list

Fields the existing record cannot fill, because they were never captured.
{c["field_gaps"]} of them.

| id | field | why it cannot be filled |
|---|---|---|
{field_gaps}

Coverage limits, which are a different kind of gap: the search did not reach
these, rather than reaching them and failing to write it down.
{c["coverage_gaps"]} of them.

| id | limit | detail |
|---|---|---|
{coverage_gaps}

## S.14 Regenerating this appendix

    {CMD}

Both this file and `results/prisma_s_rows.csv` are written by
`colophon/prisma.py` from the data in `colophon/prior_art.py`. Neither is
hand-edited. `tests/test_prisma.py` checks that every query in
`colophon.prior_art.QUERIES` reaches the CSV and that no row states a hit count
the record did not capture.
""")


def write_markdown(rows: list[dict], path: Path = APPENDIX) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(rows), encoding="utf-8")
    return str(path)


# --- ledger -------------------------------------------------------------------

def ledger_rows(rows: list[dict]) -> list[dict]:
    """Proposed rows, for results/pending_ledger/track_g2.json.

    Written as a proposal rather than straight into the ledger because parallel
    tracks each rewrite the whole CSV, so a direct write would drop whatever
    another track had just recorded.
    """
    c = counts(rows)
    shared = dict(
        section="G2", section_title="Prior art, search reporting", command=CMD,
        source_file="results/prisma_s_appendix.md and results/prisma_s_rows.csv",
        sop_class="all", validator="none, literature search",
        floor="not applicable, no validator involved",
        idc_index_version="", verified_on=prior_art.SEARCH_DATE,
        derived_from="PA-01",
    )
    dropped = (
        "Nothing sampled. Every entry in colophon.prior_art QUERIES, RETRIEVED, "
        "FAILED_RETRIEVALS, UNVERIFIED and NEIGHBOURS reaches a row. What is "
        "absent is absent from the record itself, not from this rendering of "
        "it, and is enumerated as GAP-01 through GAP-%02d in "
        "results/prisma_s_appendix.md." % len(GAPS)
    )
    status_counts = ", ".join("%s %d" % (s, c["prisma_status"][s])
                              for s in sorted(c["prisma_status"]))

    return [
        dict(id="G2-01", claim=(
            "The prior-art search is reported against the 16 PRISMA-S items, "
            "with each item answered from the record as it stands rather than "
            "from what the search could have captured."),
            status="MEASURED",
            value="%d PRISMA-S items: %s" % (c["prisma_items"], status_counts),
            n=str(c["prisma_status"].get("reported", 0)),
            denominator=str(c["prisma_items"]),
            status_note=(
                "PRISMA-S is a reporting standard for systematic review "
                "searches. This was a one-day web and API search with no "
                "protocol, no librarian and no second screener. The structure "
                "is borrowed and every departure is stated in section S.1."),
            dropped=dropped,
            pinned_by_test="tests/test_prisma.py::test_prisma_s_items_are_all_answered",
            **shared),

        dict(id="G2-02", claim=(
            "Most recorded queries carry no hit count, so their counts cannot "
            "be compared against a re-run."),
            status="MEASURED",
            value="%d of %d query rows carry a hit count captured at search "
                  "time; %d do not" % (c["hits_captured"], c["query_rows"],
                                       c["hits_not_captured"]),
            n=str(c["hits_captured"]), denominator=str(c["query_rows"]),
            status_note=(
                "The denominator excludes rows that retrieved one known record "
                "by URL or identifier, because a hit count does not arise for "
                "them. Every hit count in the appendix is transcribed from the "
                "recorded string it came from and none is reconstructed."),
            dropped=dropped,
            pinned_by_test="tests/test_prisma.py::test_no_row_claims_an_uncaptured_hit_count",
            **shared),

        dict(id="G2-03", claim=(
            "Stated as a rule: a negative prior-art claim is auditable if and "
            "only if a third party can re-run every recorded query against the "
            "same source and reproduce the hit count within a stated tolerance, "
            "and every record screened out has a recorded reason. This search "
            "meets the first condition for a small minority of its query rows "
            "and the second only for the records in its excluded register."),
            status="MEASURED",
            value="condition (a) met for %d of %d query rows; condition (b) met "
                  "for %d screened-out records, the only ones with a recorded "
                  "reason" % (c["hits_captured"], c["query_rows"],
                              c["by_type"].get("excluded_record", 0)),
            n=str(c["hits_captured"]), denominator=str(c["query_rows"]),
            status_note=(
                "Reported as a failure against the project's own rule rather "
                "than softened. The negative claim is auditable in the weak "
                "sense that its queries can be re-issued and its verdict "
                "re-tested, and not in the strong sense that its counts can be "
                "reproduced."),
            dropped=dropped,
            pinned_by_test="tests/test_prisma.py::test_the_auditability_rule_is_stated_and_applied",
            **shared),

        dict(id="G2-04", claim=(
            "Hit counts from general web search are not reproducible in the way "
            "a database query is, and general web search is the source for most "
            "of this search's query rows. No tolerance can be stated for them."),
            status="MEASURED",
            value="%d of %d query rows were issued against a general web search "
                  "whose engine is not recorded" % (c["web_query_rows"],
                                                    c["query_rows"]),
            n=str(c["web_query_rows"]), denominator=str(c["query_rows"]),
            status_note=(
                "Tolerances are stated per source class in appendix section "
                "S.3: within 5 percent for a named bibliographic index, binary "
                "presence for a single record page, and none statable for "
                "general web search."),
            dropped=dropped,
            pinned_by_test="tests/test_prisma.py::test_web_search_rows_never_state_a_hit_count",
            **shared),

        dict(id="G2-05", claim=(
            "The existing search record cannot fill a defined set of PRISMA-S "
            "style fields, and each one is named rather than left blank."),
            status="MEASURED",
            value="%d fields the record cannot fill, plus %d coverage limits"
                  % (c["field_gaps"], c["coverage_gaps"]),
            n=str(c["field_gaps"]), denominator=str(len(GAPS)),
            status_note=(
                "A field gap is a reporting defect that instrumenting the "
                "search would have prevented. A coverage limit is ground the "
                "search did not reach. They are listed separately because the "
                "remedies differ."),
            dropped=dropped,
            pinned_by_test="tests/test_prisma.py::test_every_gap_reaches_the_appendix",
            **shared),

        dict(id="G2-06", claim=(
            "Most included records have no entry in the recorded retrieval log, "
            "so the count of direct retrievals is a floor rather than a total."),
            status="MEASURED",
            value="%d of %d included records have no matching URL in "
                  "colophon.prior_art.RETRIEVED" % (c["included_unlogged"],
                                                    c["included"]),
            n=str(c["included_unlogged"]), denominator=str(c["included"]),
            status_note=(
                "The record states each nearest neighbour was retrieved and "
                "read. The retrieval log lists fewer of them than that, so the "
                "log is partial. Found by generating this appendix, not by "
                "reading the file."),
            dropped=dropped,
            pinned_by_test="tests/test_prisma.py::test_included_records_are_checked_against_the_retrieval_log",
            **shared),

        dict(id="G2-07", claim=(
            "No repository, issue tracker or documentation site was searched "
            "systematically, and the Posda source that two pending claims rest "
            "on was never retrieved."),
            status="MEASURED",
            value="0 recorded retrievals of Posda source code or database "
                  "schema; PA-08 and PA-09 remain PENDING for that reason",
            n="0", denominator=str(len(prior_art.RETRIEVED)),
            status_note=(
                "Grey literature entered this record only where general web "
                "search surfaced it. This is why the closest prior work is the "
                "hardest part of the record to audit."),
            dropped=dropped,
            derived_from="PA-01,PA-08,PA-09",
            pinned_by_test="tests/test_prisma.py::test_grey_literature_is_reported_as_unsystematic",
            **{k: v for k, v in shared.items() if k != "derived_from"}),
    ] + pa07_outcome()


PA07_NOTE = (
    "The venues are now carried as machine-readable source_not_searched rows in "
    "results/prisma_s_rows.csv and listed in appendix section S.12, so the "
    "unsearched set is enumerable rather than described in prose. The pass "
    "itself is still unrun, so the status and the value are unchanged."
)


def pa07_outcome(path=None) -> list[dict]:
    """An outcome note on PA-07, copied from the ledger rather than retyped.

    A pre-existing claim is never reworded. The row is read back from the
    ledger and every field is carried across untouched except `status_note`,
    which that row has never carried. Copying instead of retyping is what makes
    "reproduced exactly" a property of the code rather than an assertion in a
    commit message. If PA-07 is absent, nothing is proposed.
    """
    rows = ledger.load(path) if path else ledger.load()
    for row in rows:
        if row["id"] != "PA-07":
            continue
        out = dict(row)
        out.pop("date", None)
        out["status_note"] = PA07_NOTE
        return [out]
    return []


def write_pending_ledger(rows: list[dict], path: Path = PENDING) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger_rows(rows), indent=2), encoding="utf-8")
    return str(path)


def main(argv=None) -> int:
    rows = build_rows()
    c = counts(rows)
    print("wrote %s" % write_csv(rows))
    print("wrote %s" % write_markdown(rows))
    print("wrote %s" % write_pending_ledger(rows))
    print("%d rows, %d query rows, %d with a captured hit count, %d without"
          % (c["rows"], c["query_rows"], c["hits_captured"],
             c["hits_not_captured"]))
    print("gaps: %d fields not captured, %d coverage limits"
          % (c["field_gaps"], c["coverage_gaps"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
