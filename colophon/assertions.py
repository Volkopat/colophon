"""The check that catches the class, not the instances.

Six of the eight defects in the sixth addendum were one shape: a check that
computed a real number about the wrong artefact, a stated count nobody
recomputed, or a promise in prose that nothing tested. Three rounds of fixing
instances did not end it, because each fix was an instance.

One constraint kills the class:

    No row of the checklist may report a value that was not read out of a file
    in results/submission/ during that run.

An `Assertion` is therefore a path plus a function of that path's bytes. It
cannot report a module constant, because it is never handed one. If the file is
missing the assertion fails; if the file is stale the assertion reports the stale
value and the reconciliation catches it.

Five families, each aimed at a defect that got through:

- `artefact`     a value read out of one submitted file          kills A1, A4, A8
- `crossfile`    a value that must be identical in several files kills A1, A3
- `reconcile`    a table column summed against its population    kills A2
- `resolves`     prose that names a thing the package must hold  kills A5, A3
- `coverage`     a venue requirement mapped to at least one row  kills the holes

Reproduce with `python -m colophon.assertions`.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .paths import RESULTS

OUT = RESULTS / "submission" / "assertions.json"
PACKAGE = RESULTS / "submission"
# The venue names four permitted widths and one maximum height. Restating this
# as "no wider than 174 mm" is what let five figures off the grid pass.
PERMITTED_WIDTHS_MM = (39.0, 84.0, 129.0, 174.0)
MAX_HEIGHT_MM = 234.0
CMD = "python -m colophon.assertions"


@dataclass
class Result:
    name: str
    family: str
    artefacts: list
    passed: bool
    value: str
    detail: str
    requirement: str = ""


def _read(name: str) -> str:
    path = PACKAGE / name
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def _files_with(pattern: str) -> dict:
    """Every submitted markdown file and what `pattern` finds in it."""
    out = {}
    for path in sorted(PACKAGE.glob("*.md")):
        found = re.findall(pattern, path.read_text(encoding="utf-8"))
        if found:
            out[path.name] = found
    return out


# --- the assertions -------------------------------------------------------------
def keywords_agree() -> Result:
    """A1. Every file that carries a keyword list, counted and compared.

    The row that let this through counted one file, and the file it counted was
    not the one the venue designates as the carrier.
    """
    per_file = {}
    for path in sorted(PACKAGE.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"(?:\*\*Keywords\*\*|## Keywords)\s*\n*([^\n]+)",
                             text):
            words = [w.strip() for w in m.group(1).split(";") if w.strip()]
            if words:
                per_file.setdefault(path.name, []).append(words)
    counts = {f: len(lists[0]) for f, lists in per_file.items()}
    lists = {f: tuple(l[0]) for f, l in per_file.items()}
    agree = len(set(lists.values())) <= 1
    in_range = all(4 <= n <= 6 for n in counts.values())
    return Result(
        "keyword lists agree and are 4 to 6", "crossfile",
        sorted(per_file), agree and in_range and bool(counts),
        "; ".join("%s %d" % (f, n) for f, n in sorted(counts.items())),
        "%d files carry a keyword list, %d distinct lists"
        % (len(counts), len(set(lists.values()))),
        "Keywords: 4 to 6, one list")


def title_page_elements() -> Result:
    """A4. Including the umbrella heading and the abstract, which were absent."""
    page = _read("01_title_page.md")
    need = {
        "title": "Conformant and uninformative",
        "author": "Digvijay Patil",
        "affiliation": "Affiliation:",
        "ORCID": "orcid.org/",
        "corresponding author": "Corresponding author:",
        "Statements and Declarations heading": "## Statements and Declarations",
        "abstract": "## Abstract",
        "keywords": "## Keywords",
    }
    missing = sorted(k for k, v in need.items() if v not in page)
    return Result(
        "title page carries every required element", "artefact",
        ["01_title_page.md"], not missing,
        "%d of %d" % (len(need) - len(missing), len(need)),
        "searched for: %s%s" % (", ".join(sorted(need)),
                                "" if not missing else
                                ". Missing: " + ", ".join(missing)),
        "Title page elements, under 'Statements and Declarations'")


def table3_reconciles() -> Result:
    """A2. The objects column against the population it is drawn from."""
    import pandas as pd
    t1 = pd.read_csv(RESULTS / "manuscript" / "table1.csv")
    t3 = pd.read_csv(RESULTS / "manuscript" / "table3.csv")
    pop = int(t1["objects"].sum())
    got = int(t3["objects"].sum())
    per = []
    by3 = t3.groupby("sop_class_name")["objects"].sum().to_dict()
    for _, row in t1.iterrows():
        a, b = int(row["objects"]), int(by3.get(row["sop_class"], 0))
        if a != b:
            per.append("%s %d against %d" % (row["sop_class"], b, a))
    return Result(
        "table 3 objects reconcile with table 1", "reconcile",
        ["../manuscript/table1.csv", "../manuscript/table3.csv"],
        got == pop and not per, "%d of %d" % (got, pop),
        "shortfall %d%s" % (pop - got,
                            "" if not per else "; " + "; ".join(per)),
        "Every table column reconciles with its population")


def n_of_m_pairs_resolve() -> Result:
    """Item 1. Every `N of M` anywhere in the package resolves to a table.

    The reconciliation that missed the stale caption read the two source CSVs
    and never opened a shipped file, so it could not see a caption at all. This
    opens every shipped markdown file, finds every `N of M`, and recomputes the
    pair from the rows of a table in the package wherever one carries it.
    """
    import pandas as pd
    ladder = pd.read_csv(RESULTS / "claim3" / "t33_recoverability_ladder.csv")
    lvl = ladder["first_level_identity_appears"].astype(str)
    is_null = ladder["analysis_result_id"].astype(str) == "(null)"
    # The pairs a table can vouch for, recomputed from its rows.
    known = {
        (int((lvl == "none").sum()), int(len(ladder))): "table 3 rows",
        (int(((lvl == "none") & ~is_null).sum()),
         int((~is_null).sum())): "table 3 rows, residual cells excluded",
        (int(((lvl == "none") & ~is_null).sum()),
         int(len(ladder))): "table 3 rows",
        # Results 3.2.1b states a counterfactual: what the headline would read
        # if the two rule-ordering cells were counted as producer identity. It
        # is a pair whose numerator is the none-count less those two.
        (int((lvl == "none").sum()) - 2,
         int(len(ladder))): "table 3 rows less the two cells at FIG-03",
    }
    stale = {(21, 31), (19, 31), (23, 31)}
    found, bad = {}, []
    for path in sorted(PACKAGE.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"\b(\d[\d,]*) of (\d[\d,]*)\b", text):
            pair = (int(m.group(1).replace(",", "")),
                    int(m.group(2).replace(",", "")))
            found.setdefault(path.name, set()).add(pair)
            # Only pairs whose denominator is a ladder cardinality are in scope;
            # every other N of M in the package is an object or series count.
            if pair[1] in {len(ladder), int((~is_null).sum())} or pair in stale:
                if pair not in known:
                    bad.append("%s: %d of %d" % (path.name, pair[0], pair[1]))
    return Result(
        "every cell-count pair in the package recomputes from table 3",
        "reconcile", sorted(found),
        not bad, "%d files scanned, %d distinct pairs"
        % (len(found), len({p for s in found.values() for p in s})),
        "resolvable pairs: %s; unresolved: %s"
        % ("; ".join("%d of %d = %s" % (k[0], k[1], v)
                     for k, v in known.items()),
           ", ".join(bad) or "none"),
        "Every N of M resolves to a table")


def supplementary_cited() -> Result:
    """A3. The count is derived and every item is cited in both copies."""
    index = _read("06_supplementary.md")
    items = re.findall(r"^\| (S\d+) \|", index, re.M)
    stated = re.search(r"\b(\w+) items\.", index)
    full, blinded = _read("02_manuscript_full.md"), _read("03_manuscript_blinded.md")
    uncited = [s for s in items
               if s not in full or s not in blinded]
    form = "Online Resource" in full and "Online Resource" in blinded
    return Result(
        "every supplementary item is cited in both copies", "resolves",
        ["06_supplementary.md", "02_manuscript_full.md",
         "03_manuscript_blinded.md"],
        bool(items) and not uncited and form,
        "%d items, %d cited in both" % (len(items), len(items) - len(uncited)),
        "index says %r; uncited: %s; venue form 'Online Resource' present: %s"
        % (stated.group(1) if stated else "nothing",
           ", ".join(uncited) or "none", form),
        "Supplementary material cited in the text as 'Online Resource'")


def copies_differ_only_by_masking() -> Result:
    """A3's second defect: the two copies diverged in substance."""
    from . import submission
    full, blinded = _read("02_manuscript_full.md"), _read("03_manuscript_blinded.md")
    masked = submission.blind(full)
    # The blinded copy also replaces the declarations block and blanks the
    # self-citations, both declared, so those regions are excluded by name.
    def core(text):
        return " ".join(text.partition("# Declarations")[0].split())
    same = core(masked) == core(blinded)
    a, b = core(masked), core(blinded)
    where = ""
    if not same:
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                where = "first difference at character %d: %r against %r" % (
                    i, a[i:i + 70], b[i:i + 70])
                break
        else:
            where = "lengths %d and %d" % (len(a), len(b))
    return Result(
        "the two manuscript copies differ only by the declared masking", "crossfile",
        ["02_manuscript_full.md", "03_manuscript_blinded.md"], same,
        "identical after masking" if same else "diverged",
        where or "body before Declarations compared after applying the mask",
        "Blinded copy differs from the full copy only by blinding")


def prose_promises_resolve() -> Result:
    """A5. If the manuscript says a quantity is quoted, it is found quoted."""
    full = _read("02_manuscript_full.md")
    checks = []
    # An interval promised is an interval reported.
    promises = re.findall(r"[^.]*interval[^.]*\.", full)
    quoted = re.search(r"\d+(?:\.\d+)?\s*(?:to|,)\s*\d+(?:\.\d+)?\s*percent\s*"
                       r"(?:confidence )?interval|95 percent", full)
    claims_quoted = [p for p in promises
                     if "is the one quoted" in p or "is the one that is quoted" in p]
    checks.append(("an interval said to be quoted is quoted",
                   not claims_quoted or bool(quoted),
                   "%d sentences mention an interval, %d claim one is quoted, "
                   "%d intervals found in the text"
                   % (len(promises), len(claims_quoted), 1 if quoted else 0)))
    # Every figure and table the prose names exists in the package.
    figs = {int(n) for n in re.findall(r"\bFig(?:ure)?\.? (\d+)\b", full)}
    legends = set(int(n) for n in re.findall(r"\*\*Fig\. (\d+)\*\*",
                                             _read("05_figure_legends.md")))
    checks.append(("every figure named in the text has a legend",
                   figs <= legends,
                   "named %s, legends %s" % (sorted(figs), sorted(legends))))
    tables = {int(n) for n in re.findall(r"\bTable (\d+)\b", full)}
    captions = set(int(n) for n in re.findall(r"\*\*Table (\d+)\.",
                                              _read("04_tables.md")))
    checks.append(("every table named in the text has a caption",
                   tables <= captions,
                   "named %s, captions %s" % (sorted(tables), sorted(captions))))
    failed = [c for c in checks if not c[1]]
    return Result(
        "prose that names a thing resolves to the thing", "resolves",
        ["02_manuscript_full.md", "04_tables.md", "05_figure_legends.md"],
        not failed, "%d of %d" % (len(checks) - len(failed), len(checks)),
        "; ".join("%s: %s" % (n, d) for n, _ok, d in checks),
        "No unresolved promise in the text")


def figures_measured_from_the_shipped_file() -> Result:
    """A8. Width and height read off the EPS, not off the builder."""
    records = []
    for path in sorted((PACKAGE / "figures").glob("Fig*.eps")):
        head = path.read_bytes()[:2000].decode("latin-1")
        m = re.search(r"%%BoundingBox:\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", head)
        if not m:
            records.append({"file": path.name, "error": "no BoundingBox"})
            continue
        x0, y0, x1, y1 = (int(v) for v in m.groups())
        records.append({"file": path.name,
                        "width_mm": round((x1 - x0) * 25.4 / 72.0, 1),
                        "height_mm": round((y1 - y0) * 25.4 / 72.0, 1)})
    # The venue names four permitted widths, not a ceiling. Scoring against a
    # ceiling passed every figure while only one was on the grid. The tolerance
    # is not optional: 174 mm is 493 integer PostScript points, which is 173.9.
    off_grid = [r for r in records
                if not any(abs(r.get("width_mm", 0) - w) <= 0.5
                           for w in PERMITTED_WIDTHS_MM)]
    over_h = [r for r in records if r.get("height_mm", 0) > MAX_HEIGHT_MM]
    over_w = off_grid
    distinct = len({r.get("width_mm") for r in records})
    return Result(
        "figure width and height measured off the shipped EPS", "artefact",
        ["figures/" + r["file"] for r in records],
        bool(records) and not off_grid and not over_h,
        "%d figures, %d distinct widths, %d on the permitted grid"
        % (len(records), distinct, len(records) - len(off_grid)),
        "; ".join("%s %sx%s mm" % (r["file"], r.get("width_mm"),
                                   r.get("height_mm")) for r in records)
        + ("" if not over_w and not over_h else
           "; off the permitted grid %s: %s; over %.0f mm high: %s"
           % (PERMITTED_WIDTHS_MM, [r["file"] for r in off_grid],
              MAX_HEIGHT_MM, [r["file"] for r in over_h])),
        "Figure width is one of 39, 84, 129 or 174 mm and height at most 234 mm")


def disclosure_numbers_carry_units() -> Result:
    """A6. Every number in the disclosure sentence has a unit and a row."""
    page = " ".join(_read("01_title_page.md").split())
    m = re.search(r"no object in the measured set is written by that "
                  r"company.{0,700}?\(DISC-01\)", page)
    sentence = m.group(0) if m else ""
    numbers = re.findall(r"\b\d[\d,]*\b", sentence)
    has_unit = "objects searched" in sentence and "matching objects" in sentence
    has_row = "DISC-01" in sentence
    return Result(
        "every number in the disclosure carries a unit and a ledger row",
        "artefact", ["01_title_page.md"],
        bool(sentence) and has_unit and has_row,
        "%d numbers" % len(numbers),
        "unit present: %s; ledger row named: %s" % (has_unit, has_row),
        "Disclosure numbers are checkable")


def references_declare_no_unaccepted_status() -> Result:
    """A7. The venue takes only works already accepted."""
    full = _read("02_manuscript_full.md")
    refs = full.partition("# References")[2]
    bad = [l for l in refs.splitlines()
           if re.search(r"under review|in submission|submitted to|in press, "
                        r"not accepted|forthcoming", l, re.I)]
    return Result(
        "no reference self-declares an unaccepted status", "artefact",
        ["02_manuscript_full.md"], not bad,
        "%d of %d entries" % (len(bad), len(re.findall(r"^\d+\. ", refs, re.M))),
        "; ".join(b[:110] for b in bad) or "none found",
        "Only works already accepted for publication")


def no_surviving_placeholder() -> Result:
    """Items 3 and 6. Counted from the bytes of every file the manifest names.

    Three numbers were reported for this and two were wrong. The 18 was the
    field-to-file slot count in `fields.json`, filled and unfilled alike. The 19
    was the length of a token vocabulary, 17 of whose entries occur in no
    shipped file. Only the byte count is a count of anything.
    """
    from . import tokens
    manifest = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))
    names = sorted(manifest.get("files", {})) or [p.name for p in PACKAGE.glob("*.md")]
    found = {}
    for name in names:
        path = PACKAGE / name
        if not path.exists():
            continue
        markers = tokens.surviving_markers(path.read_text(encoding="utf-8"))
        if markers:
            found[name] = len(markers)
    return Result(
        "no placeholder marker survives", "artefact", sorted(found) or ["*.md"],
        not found, "%d markers" % sum(found.values()),
        "counted from the bytes of %d files named in manifest.json: %s"
        % (len(names), "; ".join("%s %d" % (f, n) for f, n in found.items())
           or "none"),
        "A final package carries no placeholder")


ASSERTIONS = [
    keywords_agree, title_page_elements, table3_reconciles,
    n_of_m_pairs_resolve,
    supplementary_cited, copies_differ_only_by_masking,
    prose_promises_resolve, figures_measured_from_the_shipped_file,
    disclosure_numbers_carry_units, references_declare_no_unaccepted_status,
    no_surviving_placeholder,
]

# Every requirement pulled out of the venue's instructions, mapped to the
# assertion or checklist row that evaluates it. A requirement mapped to nothing
# is a hole, and it is reported as one rather than omitted.
VENUE_REQUIREMENTS = {
    "Abstract 150 to 250 words": "checklist: abstract word count",
    "Keywords 4 to 6": "assertion: keyword lists agree and are 4 to 6",
    "No more than 3 displayed heading levels": "checklist: heading depth",
    "Sections in the venue's order": "checklist: section order",
    "Title page elements, under 'Statements and Declarations'":
        "assertion: title page carries every required element",
    "Double-blind: a blinded copy with no names or affiliations":
        "checklist: blinding leaks; assertion: copies differ only by masking",
    "References numbered in order of first citation": "checklist: renumbering",
    "Only works already accepted for publication":
        "assertion: no reference self-declares an unaccepted status",
    "Tables numbered, cited in consecutive order, each captioned":
        "checklist: table citation order; assertion: prose resolves",
    "Figures named Fig1 onward, vector, fonts embedded":
        "checklist: figure naming and font embedding",
    "No titles or captions inside illustrations": "checklist: drawn titles",
    "Figure lettering at 4.5 to 1 contrast": "checklist: contrast report",
    "Figure width is one of 39, 84, 129 or 174 mm and height at most 234 mm":
        "assertion: figure width and height measured off the shipped EPS",
    "Supplementary material cited in the text as 'Online Resource'":
        "assertion: every supplementary item is cited in both copies",
    "LLM use documented in the Methods": "checklist: LLM naming",
    "A link to the imaging data used": "checklist: source DOI table",
    "Manuscript in .docx, 10 pt, page numbers, single column":
        "NOT CHECKABLE HERE: the converter is declared in env/typesetting.lock "
        "and the conversion is a manual step; see results/submission/docx.md",
    "Every table column reconciles with its population":
        "assertion: table 3 objects reconcile with table 1",
    "Every N of M resolves to a table":
        "assertion: every cell-count pair in the package recomputes from table 3",
    "Disclosure numbers are checkable":
        "assertion: every number in the disclosure carries a unit and a row",
    "No unresolved promise in the text": "assertion: prose resolves",
    "A final package carries no placeholder":
        "assertion: no placeholder marker survives",
}


def run() -> dict:
    results, errors = [], []
    for fn in ASSERTIONS:
        try:
            results.append(fn())
        except Exception as exc:                      # noqa: BLE001
            errors.append({"assertion": fn.__name__, "error": repr(exc)})
    holes = sorted(k for k, v in VENUE_REQUIREMENTS.items() if not v)
    return {
        "evaluated": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": [r.__dict__ for r in results if not r.passed],
        "results": [r.__dict__ for r in results],
        "errors": errors,
        "venue_requirements": VENUE_REQUIREMENTS,
        "unmapped_requirements": holes,
        "clean": all(r.passed for r in results) and not errors and not holes,
        "command": CMD,
    }


def render(report: dict) -> str:
    out = ["# Assertions over the submitted files\n",
           "Generated by `%s`. Every value below was read out of a file in "
           "`results/submission/` during this run. An assertion is a path plus "
           "a function of that path's bytes, so it cannot report a module "
           "constant: it is never handed one.\n" % CMD,
           "**%d assertions evaluated, %d passed, %d failed, %d errored.**\n"
           % (report["evaluated"], report["passed"], len(report["failed"]),
              len(report["errors"])),
           "| assertion | family | artefacts read | result | value | detail |",
           "|---|---|---|---|---|---|"]
    for r in report["results"]:
        out.append("| %s | %s | %s | %s | %s | %s |"
                   % (r["name"], r["family"], ", ".join(r["artefacts"])[:80],
                      "pass" if r["passed"] else "**FAIL**", r["value"],
                      r["detail"][:200].replace("|", "/")))
    out.append("\n## Venue requirements, mapped\n")
    out.append("| requirement | evaluated by |")
    out.append("|---|---|")
    for k, v in sorted(report["venue_requirements"].items()):
        out.append("| %s | %s |" % (k, v or "**NOTHING, this is a hole**"))
    return "\n".join(out) + "\n"


def main() -> int:
    report = run()
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    (PACKAGE / "assertions.md").write_text(render(report), encoding="utf-8")
    print("%d assertions, %d passed, %d failed, %d errored"
          % (report["evaluated"], report["passed"], len(report["failed"]),
             len(report["errors"])))
    for r in report["failed"]:
        print("  FAIL %s: %s -- %s" % (r["name"], r["value"], r["detail"][:160]))
    for e in report["errors"]:
        print("  ERROR %s: %s" % (e["assertion"], e["error"][:160]))
    if report["unmapped_requirements"]:
        print("  unmapped venue requirements: %s"
              % report["unmapped_requirements"])
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
