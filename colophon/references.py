"""The reference list, as data rather than as prose.

`results/manuscript/references.md` was hand-written, which is the state in which
a reference silently drifts from the record it points at: a volume number typed
once is a volume number nobody checks again. This module holds the list as
entries, takes every field it can from Crossref rather than from anybody's
memory, and renders the list.

Two renderings, from the same entries:

- `render_repo()` writes `results/manuscript/references.md`, grouped by kind,
  which is the form the repository and the preprint use.
- `render_numbered()` writes the venue's form, numbered by order of first
  citation, which is what `colophon.submission` puts in the submission package.

Neither is retyped from the other, so the two cannot disagree about what a
reference says. They disagree only about order and punctuation, which is what a
citation style is.

The Crossref metadata is fetched once into
`results/manuscript/references_crossref.json` with its retrieval timestamp, and
every later run reads that file. Nothing here touches the network unless
`fetch_crossref()` is called explicitly.

Reproduce with `python -m colophon.references`.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import __version__
from .paths import RESULTS

MANUSCRIPT = RESULTS / "manuscript"
CROSSREF = MANUSCRIPT / "references_crossref.json"
OUT_MD = MANUSCRIPT / "references.md"

# Group headings, in the order the repository rendering prints them.
GROUPS = [
    ("literature", "Literature"),
    ("standard", "The standard, and the documents that change it"),
    ("tool", "Tools, each at the version that ran"),
    ("producer", "Written from the producing side"),
    ("chains", "The three chains checked at primary source"),
    ("prior", "Prior work by this author"),
    ("this", "This study"),
]

# The entries, in the order that fixes the repository numbering. The in-text
# markers in the manuscript are against this order, so an entry is appended
# rather than inserted, and a test asserts the order has not moved.
#
# `doi` entries take authors, title, journal, volume, pages and year from the
# Crossref cache. Everything else carries its fields here, because no registry
# holds them: a Correction Proposal's status lives in a status table, a tool's
# version lives in the environment record, and an unpublished manuscript lives
# nowhere at all.
ENTRIES: list[dict] = [
    {"key": "longpre2024", "group": "literature",
     "doi": "10.1038/s42256-024-00878-8"},
    {"key": "huang2025", "group": "literature",
     "doi": "10.1186/s13059-025-03725-0"},
    {"key": "clark2013", "group": "literature",
     "doi": "10.1007/s10278-013-9622-7"},
    {"key": "prior2017", "group": "literature",
     "doi": "10.1038/sdata.2017.124"},
    {"key": "bennett2018", "group": "literature",
     "doi": "10.1007/s10278-018-0097-4"},
    {"key": "fedorov2021", "group": "literature",
     "doi": "10.1158/0008-5472.CAN-21-0950"},
    {"key": "krishnaswamy2024", "group": "literature", "kind": "preprint",
     "authors": ["Krishnaswamy D", "Thiriveedhi VK", "Ciausu C", "Clunie D",
                 "Pieper S", "Kikinis R", "Fedorov A"],
     "title": "Rule-based outlier detection of AI-generated anatomy segmentations",
     "year": 2024, "archive": "arXiv:2406.14486 [eess.IV]",
     "doi_text": "10.48550/arXiv.2406.14486",
     "note": "Cited as the preprint because no journal or proceedings version "
             "was found at the time of writing."},

    {"key": "ps33", "group": "standard", "kind": "standard",
     "issuer": "National Electrical Manufacturers Association",
     "title": "Digital Imaging and Communications in Medicine (DICOM) Standard, "
              "Part 3: Information Object Definitions",
     "designation": "PS3.3-2026c", "place": "Rosslyn, VA", "year": 2026,
     "url": "https://dicom.nema.org/medical/dicom/2026c/",
     "accessed": "2026-08-02",
     "note": "Read from the DocBook distribution pre-seeded on the measurement "
             "machine under PRE-04, `part03.xml`, 25,448,510 bytes, rather than "
             "over the network at run time."},
    {"key": "ps35", "group": "standard", "kind": "standard",
     "issuer": "National Electrical Manufacturers Association",
     "title": "Digital Imaging and Communications in Medicine (DICOM) Standard, "
              "Part 5: Data Structures and Encoding",
     "designation": "PS3.5-2026c", "place": "Rosslyn, VA", "year": 2026,
     "url": "https://dicom.nema.org/medical/dicom/2026c/",
     "accessed": "2026-08-02",
     "note": "Section 7.4.5 is the clause CP-2273 settles."},
    {"key": "cp2273", "group": "standard", "kind": "cp", "number": "CP-2273"},
    {"key": "sup243", "group": "standard", "kind": "supplement",
     "number": "Supplement 243",
     "committee": "DICOM Standards Committee, Working Group 6",
     "work_item": "2023-10-B",
     "document_status": "Final Text", "document_date": "2024-09-14",
     "url": "https://www.dicomstandard.org/News-dir/ftsup/docs/sups/sup243.pdf",
     "accessed": "2026-08-03",
     "sha256": "6b922b3bdee71a02a0de03dadebc647c848af2233c67f84f0772256f71d14e73"},
    {"key": "cp2428", "group": "standard", "kind": "cp", "number": "CP-2428"},
    {"key": "cp2320", "group": "standard", "kind": "cp", "number": "CP-2320"},
    {"key": "cp1597", "group": "standard", "kind": "cp", "number": "CP-1597"},
    {"key": "cp1258", "group": "standard", "kind": "cp", "number": "CP-1258"},
    {"key": "cp2115", "group": "standard", "kind": "cp", "number": "CP-2115"},
    {"key": "iheair", "group": "standard", "kind": "profile",
     "issuer": "IHE International",
     "title": "IHE Radiology Technical Framework Supplement, AI Results (AIR)",
     "revision": "Rev. 1.3", "document_status": "Trial Implementation",
     "document_date": "2025-08-08", "year": 2025,
     "url": "https://www.ihe.net/uploadedFiles/Documents/Radiology/"
            "IHE_RAD_Suppl_AIR_Rev1-3_TI_2025-08-08.pdf",
     "accessed": "2026-08-02",
     "sha256": "33C9E86326E8946BA2DB0B37E5FEE73A865C7B11A00201B983690FCA2ED1D964",
     "note": "Trial Implementation since 2020-07-16. The sha256 was "
             "re-verified against the pinned local copy 2026-08-03."},

    {"key": "dicom3tools", "group": "tool", "kind": "software",
     "authors": ["Clunie DA"], "title": "dicom3tools, `dciodvfy`",
     "version": "package 1.00, snapshot 20260701065818",
     "url": "https://www.dclunie.com/dicom3tools.html", "accessed": "2026-08-03",
     "note": "The binary exposes no version flag and is pinned in "
             "`results/environment.json` by sha256 and mtime. The registered "
             "pin, snapshot 20240118131615, was never satisfied; see Methods "
             "2.10."},
    {"key": "dcmtk", "group": "tool", "kind": "software",
     "authors": ["OFFIS e.V."],
     "title": "DCMTK: DICOM Toolkit, `dcmpschk`, `dcmdump`, `dcmp2pgm`",
     "version": "3.7.0, build 2025-12-15",
     "url": "https://dicom.offis.de/dcmtk", "accessed": "2026-08-03"},
    {"key": "dicomvalidator", "group": "tool", "kind": "software",
     "authors": ["pydicom project"], "title": "dicom-validator",
     "version": "0.8.2",
     "url": "https://github.com/pydicom/dicom-validator", "accessed": "2026-08-03",
     "note": "Run against a pre-seeded standard path so that no measurement "
             "depends on a network fetch at run time."},
    {"key": "pydicom", "group": "tool", "doi": "10.1118/1.3611983",
     "note": "Version 3.0.2 as run, https://github.com/pydicom/pydicom"},
    {"key": "pixelmed", "group": "tool", "kind": "software",
     "authors": ["Clunie DA"], "title": "PixelMed Java DICOM Toolkit",
     "url": "https://www.pixelmed.com/dicomtoolkit.html", "accessed": "2026-08-03",
     "note": "The `DicomInstanceValidator` jar is absent from the pinned "
             "toolchain and did not run; see ledger row V-04."},
    {"key": "highdicom", "group": "tool", "doi": "10.1007/s10278-022-00683-y",
     "note": "Version 0.28.1 as installed; the registered pin was 0.28.0, see "
             "Methods 2.10."},
    {"key": "dcmqi", "group": "tool", "doi": "10.1158/0008-5472.CAN-17-0336"},
    {"key": "idcindex", "group": "tool", "kind": "software",
     "authors": ["Imaging Data Commons"], "title": "idc-index",
     "version": "0.12.5, with idc-index-data 24.2.2, carrying IDC release v24",
     "url": "https://github.com/ImagingDataCommons/idc-index",
     "accessed": "2026-08-03"},

    {"key": "monai528", "group": "producer", "kind": "webpage",
     "authors": ["Project MONAI"],
     "title": "Contributing Equipment Sequence for DICOM SEG Writer",
     "container": "monai-deploy-app-sdk Discussion 528",
     "document_date": "2025-02-20", "year": 2025,
     "url": "https://github.com/Project-MONAI/monai-deploy-app-sdk/discussions/528",
     "accessed": "2026-08-03"},
    {"key": "murugesan2024", "group": "producer",
     "doi": "10.1038/s41597-024-03977-8"},
    {"key": "balliu2023", "group": "producer",
     "doi": "10.1109/MSEC.2023.3302956"},
    {"key": "fedorov2016", "group": "producer", "doi": "10.7717/peerj.2057"},

    {"key": "rfc8461", "group": "chains", "kind": "rfc",
     "authors": ["Margolis D", "Risher M", "Ramakrishnan B", "Brotman A",
                 "Jones J"],
     "title": "SMTP MTA Strict Transport Security (MTA-STS)",
     "number": "RFC 8461", "issuer": "IETF", "year": 2018,
     "doi_text": "10.17487/RFC8461"},
    {"key": "rfc8996", "group": "chains", "kind": "rfc",
     "authors": ["Moriarty K", "Farrell S"],
     "title": "Deprecating TLS 1.0 and TLS 1.1",
     "number": "RFC 8996, BCP 195", "issuer": "IETF", "year": 2021,
     "doi_text": "10.17487/RFC8996"},
    {"key": "rfc7919", "group": "chains", "kind": "rfc",
     "authors": ["Gillmor D"],
     "title": "Negotiated finite field Diffie-Hellman ephemeral parameters for "
              "Transport Layer Security (TLS)",
     "number": "RFC 7919", "issuer": "IETF", "year": 2016,
     "doi_text": "10.17487/RFC7919"},
    {"key": "adrian2015", "group": "chains", "doi": "10.1145/2810103.2813707"},

    {"key": "patil_spinegsps_article", "group": "prior", "kind": "manuscript",
     "authors": ["Patil D"],
     "title": "Separating conformance from trustworthiness: an end-to-end audit, "
              "and five checks, for an AI result delivered into a clinical archive",
     "year": 2026, "state": "Preprint and evaluation harness",
     "url": "https://github.com/Volkopat/spine-gsps", "accessed": "2026-08-03",
     "note": "Cited for its method. The released harness that accompanies it is "
             "the following entry and is the citable artefact; the title is as "
             "given in that harness's `CITATION.cff`."},
    {"key": "patil_spinegsps_harness", "group": "prior", "kind": "software",
     "authors": ["Patil D"],
     "title": "spine-gsps: evaluation harness for a deployed DICOM "
              "spine-labelling service",
     "version": "v1.0.1", "publisher": "Zenodo", "document_date": "2026-07-31",
     "year": 2026, "doi_text": "10.5281/zenodo.21728679",
     "url": "https://github.com/Volkopat/spine-gsps",
     "note": "Version DOI 10.5281/zenodo.21728679, concept DOI "
             "10.5281/zenodo.21728405."},
    {"key": "patil_palimpsest_article", "group": "prior", "kind": "manuscript",
     "authors": ["Patil D"],
     "title": "An on-premise, open-weights vision-language pipeline for "
              "burned-in PHI removal: detection, decision, and robustness on "
              "MIDI-B",
     "year": 2026, "state": "Preprint and reproduction harness",
     "url": "https://github.com/Volkopat/palimpsest", "accessed": "2026-08-03",
     "note": "The reproduction harness that accompanies it is the following "
             "entry and is the citable artefact; the title is as given in that "
             "harness's README."},
    {"key": "patil_palimpsest_harness", "group": "prior", "kind": "software",
     "authors": ["Patil D"],
     "title": "palimpsest: reproduction harness for burned-in PHI removal on "
              "the MIDI-B benchmark",
     "version": "1.0.0", "document_date": "2026-07-16", "year": 2026,
     "url": "https://github.com/Volkopat/palimpsest", "accessed": "2026-08-03",
     "note": "No DOI has been minted for this harness at the time of writing."},

    {"key": "colophon", "group": "this", "kind": "software",
     "authors": ["Patil D"],
     "title": "colophon: a conformance and provenance census of AI-derived "
              "DICOM objects in the NCI Imaging Data Commons",
     "version": __version__, "publisher": "Zenodo", "year": 2026,
     "url": "https://github.com/Volkopat/colophon",
     "note": "Version DOI `[FIELD: Zenodo version DOI, minted when the release "
             "is cut]`, concept DOI `[FIELD: Zenodo concept DOI]`."},
]

# Correction Proposal rows come from the pinned status table rather than from
# here, so a status this project quotes cannot drift from the status the table
# carried when it was read.
STATUS_ROWS = RESULTS / "cp" / "dicom_status_rows.json"


def _crossref() -> dict:
    if not CROSSREF.exists():
        return {}
    return json.loads(CROSSREF.read_text(encoding="utf-8")).get("records", {})


def _status() -> dict:
    if not STATUS_ROWS.exists():
        return {}
    d = json.loads(STATUS_ROWS.read_text(encoding="utf-8"))
    out = dict(d.get("correction_proposals", {}))
    out.update(d.get("supplements", {}))
    out["_retrieved"] = d.get("retrieved", "")
    out["_url"] = d.get("source_url", "")
    return out


def clean(text: str) -> str:
    """Crossref titles carry markup and typographic hyphens. Both travel badly.

    `<i>dcmqi</i>` with newlines inside it is what the dcmqi record returns, and
    U+2010 HYPHEN is what the pydicom record returns. A reference list is read
    and retyped by other people, so both are normalised to plain text here
    rather than left for a copy editor.
    """
    import re
    text = re.sub(r"<[^>]+>", "", text or "")
    for bad, good in (("‐", "-"), ("‑", "-"), ("­", ""),
                      ("–", "-"), ("’", "'")):
        text = text.replace(bad, good)
    text = " ".join(text.split())
    # Stripping the markup out of `<i>dcmqi</i>   : An Open Source Library`
    # leaves the space the tag used to occupy in front of the colon.
    return re.sub(r"\s+([:;,.])", r"\1", text)


def initials(given: str) -> str:
    """`Hugo J.W.L.` to `HJWL`, `Jean-Christophe` to `JC`, `David A.` to `DA`.

    Given names are capitalised and initials are the capitals in them, which is
    true of every name in this list and is checked by a test.
    """
    return "".join(c for c in given if c.isupper())


def load() -> list[dict]:
    """Entries with the Crossref fields merged in, in repository order."""
    cross, status = _crossref(), _status()
    out = []
    for i, entry in enumerate(ENTRIES, start=1):
        e = dict(entry)
        e["number"] = e.get("number", "")
        e["n"] = i
        doi = e.get("doi")
        if doi:
            rec = cross.get(doi.lower())
            if rec is None:
                raise KeyError("%s cites %s, which is not in the Crossref cache. "
                               "Run python -m colophon.references --fetch"
                               % (e["key"], doi))
            e["kind"] = e.get("kind", "article")
            e["authors"] = [clean("%s %s" % (a["family"], initials(a["given"])))
                            for a in rec["authors"]]
            # Crossref splits `Imperfect Forward Secrecy` from `How
            # Diffie-Hellman Fails in Practice`, and a title that stops at the
            # colon is a title a reader cannot find the paper by.
            title = clean(rec["title"])
            subtitle = clean(rec.get("subtitle", ""))
            if subtitle and subtitle.lower() not in title.lower():
                title = "%s: %s" % (title.rstrip(":."), subtitle)
            e["title"] = title
            e.setdefault("publisher", clean(rec.get("publisher", "")))
            e["container"] = clean(rec["container"])
            e["short_container"] = clean(rec["short_container"] or rec["container"])
            e["volume"] = rec["volume"]
            e["issue"] = rec["issue"]
            pages = rec["page"] or rec["article_number"]
            # `3493-3493` is what Crossref returns for a single-page abstract.
            if "-" in pages and len(set(pages.split("-"))) == 1:
                pages = pages.split("-")[0]
            e["pages"] = pages
            e["year"] = rec["year"]
            # The DOI as registered here, not as Crossref echoes it. Crossref
            # lowercases, and 10.1158/0008-5472.CAN-21-0950 is published with
            # CAN in capitals. DOIs resolve either way and readers retype what
            # they see.
            e["doi_text"] = doi
        if e.get("kind") in ("cp", "supplement"):
            row = status.get(e["number"])
            if row is None:
                raise KeyError("%s is not in the pinned DICOM status table"
                               % e["number"])
            e["title"] = row["title"]
            e["affected"] = row["affected"]
            # Two statuses, and they are different facts. The status table says
            # where the change now sits in the standard; a supplement's own
            # cover page says what the document is. Overwriting one with the
            # other loses the publication date the Discussion cites.
            e["table_status"] = row["status"]
            e.setdefault("document_status", row["status"])
            e["applies_to"] = row["applies_to"]
            e.setdefault("url", status.get("_url", ""))
            e.setdefault("accessed", status.get("_retrieved", ""))
        out.append(e)
    return out


# --- renderers ----------------------------------------------------------------
def _authors_repo(names: list[str], limit: int = 6) -> str:
    if len(names) > limit:
        return ", ".join(names[:limit]) + ", et al"
    return ", ".join(names)


def render_repo_entry(e: dict) -> str:
    """The repository and preprint form. Author-year-ish, DOI last."""
    kind = e.get("kind", "article")
    if kind == "article":
        # A proceedings paper has no volume, and rendering it as one produces
        # `Proceedings of the 22nd ACM SIGSAC Conference. 2015;:5-17`.
        if not e["volume"]:
            return _tail("%s. %s. In: %s. %s; %s:%s." % (
                _authors_repo(e["authors"]), e["title"].rstrip("."),
                e["container"], e.get("publisher", "").strip() or "n.p.",
                e["year"], e["pages"]), e)
        head = "%s. %s. %s. %s;%s%s:%s." % (
            _authors_repo(e["authors"]), e["title"].rstrip("."), e["container"],
            e["year"], e["volume"],
            "(%s)" % e["issue"] if e["issue"] else "", e["pages"])
        return _tail(head, e)
    if kind == "preprint":
        return _tail("%s. %s. %s. %s." % (_authors_repo(e["authors"]),
                                          e["title"].rstrip("."), e["archive"],
                                          e["year"]), e)
    if kind == "standard":
        return _tail("%s. %s. %s. %s: %s; %s." % (
            e["issuer"], e["title"].rstrip("."), e["designation"], e["place"],
            e["issuer"].split()[0] if False else "NEMA", e["year"]), e)
    if kind == "cp":
        return _tail("DICOM Correction Proposal %s, %s. Affects %s. Status: %s, "
                     "applied at edition %s." % (
                         e["number"], e["title"].rstrip("."),
                         _parts(e["affected"]), e["document_status"],
                         e["applies_to"]), e)
    if kind == "supplement":
        return _tail("DICOM %s, %s. %s, work item %s. Document status: %s, "
                     "publication date %s. In the standard: %s, applied at "
                     "edition %s." % (
                         e["number"], e["title"].rstrip("."), e["committee"],
                         e["work_item"], e["document_status"],
                         e["document_date"], e["table_status"],
                         e["applies_to"]), e)
    if kind == "profile":
        return _tail("%s. %s. %s, %s, %s." % (
            e["issuer"], e["title"].rstrip("."), e["revision"],
            e["document_status"], e["document_date"]), e)
    if kind == "software":
        title = e["title"].rstrip(".")
        if e.get("version"):
            title += ", version %s" % e["version"]
        head = _join([", ".join(e["authors"]), title])
        if e.get("publisher"):
            head = _join([head, e["publisher"]
                          + ("; %s" % e["document_date"]
                             if e.get("document_date") else "")])
        elif e.get("document_date"):
            head = _join([head, e["document_date"]])
        return _tail(head, e)
    if kind == "webpage":
        return _tail("%s. %s. %s, opened %s." % (
            ", ".join(e["authors"]), e["title"].rstrip("."), e["container"],
            e["document_date"]), e)
    if kind == "rfc":
        return _tail("%s. %s. %s. %s; %s." % (
            ", ".join(e["authors"]), e["title"].rstrip("."), e["number"],
            e["issuer"], e["year"]), e)
    if kind == "manuscript":
        return _tail("%s. %s. %s; %s." % (
            ", ".join(e["authors"]), e["title"].rstrip("."), e["state"],
            e["year"]), e)
    raise ValueError("no repository renderer for kind %r" % kind)


def _parts(affected: str) -> str:
    """`Parts 3,16` as the standard writes it, to `Parts 3 and 16`."""
    nums = [n.strip() for n in affected.replace("Parts", "").replace("Part", "")
            .split(",") if n.strip()]
    if len(nums) == 1:
        return "Part %s" % nums[0]
    return "Parts %s and %s" % (", ".join(nums[:-1]), nums[-1])


def _join(bits: list[str]) -> str:
    """Sentences, each ending in exactly one full stop.

    Naive joining produced `OFFIS e.V.. DCMTK` and
    `doi:10.48550/arXiv.2406.14486 Cited as the preprint`, which are the two
    ways a generated reference list looks hand-mangled.
    """
    out = ""
    for bit in bits:
        bit = bit.strip()
        if not bit:
            continue
        if out and not out.endswith((".", "?", "!")):
            out += "."
        out += (" " if out else "") + bit
    return out if out.endswith((".", "?", "!")) else out + "."


def _tail(head: str, e: dict) -> str:
    bits = [head]
    if e.get("doi_text"):
        bits.append("doi:%s" % e["doi_text"])
    if e.get("url"):
        bits.append(e["url"])
    if e.get("accessed"):
        bits.append("Retrieved %s" % e["accessed"])
    if e.get("sha256"):
        bits.append("sha256 %s" % e["sha256"])
    if e.get("note"):
        bits.append(e["note"])
    return _join(bits)


def render_jiim_entry(e: dict) -> str:
    """The venue form, from its own worked example:

        Zaidel M, Hopper K, Iyriboz T: Interactive web-based radiology teaching
        file. J Digit Imaging 12:203-204, 1999

    Authors, all of them, then a colon, then the title, then the journal name as
    abbreviated in Index Medicus, then volume, pages and year. The DOI is added
    after that, which the example does not show and which no venue rejects.
    """
    kind = e.get("kind", "article")
    if kind == "article":
        if not e["volume"]:
            return _jiim_tail("%s: %s. In: %s, %s, %s" % (
                ", ".join(e["authors"]), e["title"].rstrip("."),
                e["container"], e["pages"], e["year"]), e)
        core = "%s: %s. %s %s:%s, %s" % (
            ", ".join(e["authors"]), e["title"].rstrip("."),
            e["short_container"], e["volume"], e["pages"], e["year"])
        return _jiim_tail(core, e)
    if kind == "preprint":
        return _jiim_tail("%s: %s. %s, %s" % (
            ", ".join(e["authors"]), e["title"].rstrip("."), e["archive"],
            e["year"]), e)
    if kind == "standard":
        return _jiim_tail("%s: %s. %s, %s, %s" % (
            e["issuer"], e["title"].rstrip("."), e["designation"], e["place"],
            e["year"]), e)
    if kind == "cp":
        return _jiim_tail(
            "DICOM Standards Committee: %s, %s. Affects %s. Status %s, applied "
            "at edition %s" % (e["number"], e["title"].rstrip("."),
                               _parts(e["affected"]), e["document_status"],
                               e["applies_to"]), e)
    if kind == "supplement":
        return _jiim_tail(
            "%s: DICOM %s, %s. %s, %s, in the standard at edition %s" % (
                e["committee"], e["number"], e["title"].rstrip("."),
                e["document_status"], e["document_date"], e["applies_to"]), e)
    if kind == "profile":
        return _jiim_tail("%s: %s. %s, %s, %s" % (
            e["issuer"], e["title"].rstrip("."), e["revision"],
            e["document_status"], e["document_date"]), e)
    if kind == "software":
        core = "%s: %s" % (", ".join(e["authors"]), e["title"].rstrip("."))
        if e.get("version"):
            core += ", version %s" % e["version"]
        if e.get("publisher"):
            core += ", %s" % e["publisher"]
        core += ", %s" % e["year"] if e.get("year") else ""
        return _jiim_tail(core, e)
    if kind == "webpage":
        return _jiim_tail("%s: %s. %s, %s" % (
            ", ".join(e["authors"]), e["title"].rstrip("."), e["container"],
            e["document_date"]), e)
    if kind == "rfc":
        return _jiim_tail("%s: %s. %s, %s, %s" % (
            ", ".join(e["authors"]), e["title"].rstrip("."), e["number"],
            e["issuer"], e["year"]), e)
    if kind == "manuscript":
        return _jiim_tail("%s: %s. %s, %s" % (
            ", ".join(e["authors"]), e["title"].rstrip("."), e["state"],
            e["year"]), e)
    raise ValueError("no venue renderer for kind %r" % kind)


def _jiim_tail(core: str, e: dict) -> str:
    bits = [core]
    if e.get("doi_text"):
        bits.append("doi:%s" % e["doi_text"])
    if e.get("url") and not e.get("doi_text"):
        bits.append(e["url"])
    if e.get("accessed") and not e.get("doi_text"):
        bits.append("Accessed %s" % e["accessed"])
    return _join(bits)


PREAMBLE = """# References

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
"""

FOOTER = """
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
"""


def render_repo() -> str:
    entries = load()
    parts = [PREAMBLE]
    for group, heading in GROUPS:
        rows = [e for e in entries if e["group"] == group]
        if not rows:
            continue
        parts.append("## %s\n" % heading)
        for e in rows:
            body = render_repo_entry(e)
            parts.append("%d. %s\n" % (e["n"], _wrap(body, e["n"])))
    parts.append(FOOTER)
    return "\n".join(parts)


def _wrap(text: str, n: int, width: int = 78) -> str:
    """Wrap continuation lines under the number, the way the file already reads."""
    import textwrap
    indent = " " * (len(str(n)) + 2)
    lines = textwrap.wrap(text, width=width - len(indent),
                          break_long_words=False, break_on_hyphens=False)
    return ("\n" + indent).join(lines)


def render_numbered(order: list[int]) -> list[tuple[int, str]]:
    """The venue form, renumbered.

    `order` is the repository numbers in order of first citation. The result is
    (new number, rendered entry), so the caller can rewrite the in-text markers
    against the same mapping and the two cannot fall out of step.
    """
    entries = {e["n"]: e for e in load()}
    return [(i, render_jiim_entry(entries[old]))
            for i, old in enumerate(order, start=1)]


def fetch_crossref() -> Path:                                # pragma: no cover
    """Refresh the Crossref cache. The only function here that touches the network."""
    import datetime
    import time
    import requests
    # The polite pool, and a pause between calls. An unthrottled loop over this
    # list returns 429 partway through, which is how a cache ends up holding
    # some records at one retrieval time and some at another.
    headers = {"User-Agent": "colophon/0.1 (https://github.com/Volkopat/colophon)"}
    out = {"retrieved_utc": datetime.datetime.now(datetime.timezone.utc)
           .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "source": "https://api.crossref.org/works/<doi>", "records": {}}
    for e in ENTRIES:
        doi = e.get("doi")
        if not doi:
            continue
        r = requests.get("https://api.crossref.org/works/" + doi, timeout=90,
                         headers=headers)
        r.raise_for_status()
        time.sleep(1.0)
        m = r.json()["message"]
        out["records"][doi.lower()] = {
            "doi": m.get("DOI"), "title": (m.get("title") or [""])[0],
            "subtitle": (m.get("subtitle") or [""])[0],
            "container": (m.get("container-title") or [""])[0],
            "short_container": (m.get("short-container-title") or [""])[0],
            "volume": m.get("volume", ""), "issue": m.get("issue", ""),
            "page": m.get("page", ""), "article_number": m.get("article-number", ""),
            "year": m.get("issued", {}).get("date-parts", [[None]])[0][0],
            "type": m.get("type", ""), "publisher": m.get("publisher", ""),
            "authors": [{"family": a.get("family", ""), "given": a.get("given", "")}
                        for a in m.get("author", [])]}
    CROSSREF.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    return CROSSREF


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true",
                    help="refresh the Crossref cache over the network")
    args = ap.parse_args(argv)
    if args.fetch:
        print("wrote %s" % fetch_crossref())
    OUT_MD.write_text(render_repo(), encoding="utf-8")
    entries = load()
    print("%d entries, %d groups" % (len(entries), len({e["group"] for e in entries})))
    print("wrote %s" % OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
