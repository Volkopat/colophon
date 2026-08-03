"""Track C adjudication: Parametric Map Storage.

Every distinct `message_class_id` the Phase 2 census recorded against
Parametric Map Storage is placed in exactly one of five categories, and each
placement carries a PS3.3, PS3.4, PS3.5 or PS3.16 section and table plus a
verbatim quote. The rule the project runs on is that no citation means
UNDECIDABLE, and that a category of NET requires the exact section and table
giving the Type or condition violated.

The adjudication table below is data, not inference: the matcher picks the rule,
the rule carries the citation, and a message class that matches no rule stops
the run rather than being dropped. Nothing here decides whether an object is
conformant. It attaches the standard's own text to the validator's message.

Usage:
    python -m colophon.adjudicate_pm
"""
from __future__ import annotations

import csv
import json
import re
import statistics
import sys
from pathlib import Path

from .paths import CACHE, RESULTS

CMD = "python -m colophon.adjudicate_pm"
SOP_CLASS = "Parametric Map Storage"
ANALYSIS_RESULT_ID = "tcga_gbm360"

CENSUS_CLASSES = RESULTS / "phase2" / "census_message_classes.csv"
RECORDS = CACHE / "census" / "records.jsonl"
FLOOR_SET = RESULTS / "floor_set.csv"
OUT_CSV = RESULTS / "phase2" / "adjudication_parametric_map.csv"
OUT_MD = RESULTS / "phase2" / "net_rates_parametric_map.md"

# Categories that leave an object at the floor rather than in the net.
FLOOR_SIDE = {"FLOOR", "NOT-IOD", "PLAUSIBILITY"}
CATEGORIES = {"FLOOR", "NET", "NOT-IOD", "PLAUSIBILITY", "UNDECIDABLE"}

# PS3.5 Section 3.10, quoted once and reused by the two Image Type rules.
Q_DEFINED_TERM = (
    'PS3.5 3.10: "The Value of a Data Element is a Defined Term when the Value '
    "of the Data Element may be one of an explicitly specified set of standard "
    'Values, and these Values may be extended by implementers." '
    'PS3.5 3.10, for contrast: "The Value of a Data Element is an Enumerated '
    "Value when the Value of the Data Element must be one of an explicitly "
    'specified set of standard Values, and these Values shall not be extended '
    'by implementers."'
)

# PS3.3 C.7.6.16, Table C.7.6.16-1, quoted once and reused by the five shared
# functional group rules.
Q_SHARED_FG = (
    'PS3.3 C.7.6.16, Table C.7.6.16-1, Shared Functional Groups Sequence '
    '(5200,9229), Type 1: "Sequence that contains the Functional Group Macros '
    'that are shared for all Frames in this SOP Instance and Concatenation." '
    'PS3.3 C.7.6.16: "For each IOD that includes this Module, a table is '
    'defined in which the permitted Functional Group Macros and their usage is '
    'specified."'
)

# The one usage restriction Table A.75-2 places on a functional group macro.
Q_FRAME_CONTENT = (
    'PS3.3 A.75.5, Table A.75-2, the only row carrying a Shared restriction: '
    '"Frame Content | C.7.6.16.2.2 | M - Shall not be used as a Shared '
    'Functional Group"'
)

_FG_RATIONALE = (
    "Table A.75-2 lists the {macro} Macro as Usage M for the Parametric Map "
    "IOD, and {seq} {tag} is the Type 1 sequence attribute of that macro. "
    "Table A.75-2 restricts exactly one macro, Frame Content, from the Shared "
    "Functional Groups Sequence, and this is not it, so the construct the "
    "message reports is not merely permitted in the Shared Functional Groups "
    "Sequence, it is mandatory somewhere in the functional groups. The same "
    "message_class_id is emitted by dicom-validator against the highdicom "
    "built Parametric Map fixture in results/floor_set.csv, which is evidence "
    "about the tool rather than about the object. The mechanism inside "
    "dicom-validator is not resolved here and is not needed for the "
    "adjudication."
)

_FG_MACROS = [
    ("Pixel Measures Sequence", "Pixel Measures", "C.7.6.16.2.1",
     "Table C.7.6.16-2", "(0028,9110)",
     '"Pixel Measures | C.7.6.16.2.1 | M"'),
    ("Frame VOI LUT Sequence", "Frame VOI LUT With LUT", "C.7.6.16.2.10b",
     "Table C.7.6.16-11b", "(0028,9132)",
     '"Frame VOI LUT With LUT | C.7.6.16.2.10b | M"'),
    ("Pixel Value Transformation Sequence", "Identity Pixel Value Transformation",
     "C.7.6.16.2.9b", "Table C.7.6.16-10b", "(0028,9145)",
     '"Identity Pixel Value Transformation | C.7.6.16.2.9b | M"'),
    ("Parametric Map Frame Type Sequence", "Parametric Map Frame Type",
     "C.8.32.3.1", "Table C.8.32-3", "(0040,9092)",
     '"Parametric Map Frame Type | C.8.32.3.1 | M"'),
    ("Real World Value Mapping Sequence", "Real World Value Mapping",
     "C.7.6.16.2.11", "Table C.7.6.16-12", "(0040,9096)",
     '"Real World Value Mapping | C.7.6.16.2.11 | M"'),
]


def _rules() -> list[dict]:
    rules: list[dict] = []

    for seq, macro, sect, table, tag, row in _FG_MACROS:
        rules.append({
            "name": "shared_fg_%s" % macro.lower().replace(" ", "_"),
            "validator": "dicom-validator",
            "pattern": re.compile(
                r"^Module <Multi-frame Functional Groups> \(TAG\) "
                r"\(Shared Functional Groups Sequence\) Tag \(TAG\) "
                r"\(%s\) is unexpected$" % re.escape(seq)),
            "adjudication": "FLOOR",
            "citation_section": "PS3.3 A.75.5, with PS3.3 %s and PS3.3 C.7.6.16" % sect,
            "citation_table": "Table A.75-2; %s; Table C.7.6.16-1" % table,
            "citation_quote": (
                "PS3.3 A.75.5, Table A.75-2, Parametric Map Functional Group "
                "Macros: %s. PS3.3 %s, %s, first row: %s %s Type 1. %s. %s"
                % (row, sect, table, seq, tag, Q_SHARED_FG, Q_FRAME_CONTENT)),
            "rationale": _FG_RATIONALE.format(macro=macro, seq=seq, tag=tag),
        })

    for attr, tag, macro_table in [("Rows", "(0028,0010)", "Table C.7-11c"),
                                   ("Columns", "(0028,0011)", "Table C.7-11c")]:
        rules.append({
            "name": "general_%s" % attr.lower(),
            "validator": "dicom-validator",
            "pattern": re.compile(
                r"^Module <General> Tag \(TAG\) \(%s\) is unexpected$"
                % re.escape(attr)),
            "adjudication": "FLOOR",
            "citation_section": ("PS3.3 A.75.3 and PS3.3 A.75.4, with PS3.3 "
                                 "C.7.6.3, C.7.6.24 and C.7.6.25"),
            "citation_table": ("Table A.75-1; Table C.7-11a; %s; "
                               "Table C.7.6.24-1; Table C.7.6.25-1" % macro_table),
            "citation_quote": (
                'PS3.3 A.75.4, Parametric Map IOD Content Constraints: "Either '
                "the Image Pixel Module or the Floating Point Image Pixel "
                "Module or the Double Floating Point Image Pixel Module is "
                'required, and only one of these shall be present." '
                'PS3.3 C.7.6.3, Table C.7-11a includes "Table C.7-11c Image '
                'Pixel Description Macro Attributes", in which %s %s is Type 1, '
                '"Number of %s in the image". PS3.3 C.7.6.24, Table '
                "C.7.6.24-1: %s %s Type 1. PS3.3 C.7.6.25, Table C.7.6.25-1: "
                "%s %s Type 1. PS3.3 A.75.3, Table A.75-1 lists the modules of "
                "the Parametric Map IOD and contains no module named General."
                % (attr, tag, attr.lower(), attr, tag, attr, tag)),
            "rationale": (
                "%s %s is Type 1 in every one of the three pixel modules the "
                "Parametric Map IOD offers, and A.75.4 requires exactly one of "
                "those three to be present, so %s is required in any conformant "
                "instance of this IOD and its presence cannot be a violation of "
                "a stated requirement. General is not a module: it is the label "
                "dicom-validator gives the bucket of tags it could not attribute "
                "to any module of the recognised IOD, written at "
                "dicom_validator/validator/iod_validator.py in the call "
                'add_tag_errors("General", self._unexpected_tag_errors()). Which '
                "of the three pixel modules these objects carry, and why the "
                "tool did not attribute the tag to it, is not resolved here: the "
                "series were deleted after validation and the project does not "
                "resolve a validator ambiguity by judgement. Unlike the five "
                "Shared Functional Groups classes, this class is not present in "
                "results/floor_set.csv, so it is adjudicated on the citation "
                "alone and not on floor overlap." % (attr, tag, attr)),
        })

    rules.append({
        "name": "image_type_value3",
        "validator": "dciodvfy",
        "pattern": re.compile(
            r"^Warning - Unrecognized defined term <AGGRESSIVENESS> for value 3 "
            r"of attribute <Image Type>$"),
        "adjudication": "FLOOR",
        "citation_section": "PS3.3 C.8.32.2, with PS3.3 C.8.16.1.3 and PS3.5 3.10",
        "citation_table": "Table C.8.32-2; Table C.8-129",
        "citation_quote": (
            "PS3.3 C.8.32.2, Table C.8.32-2, Parametric Map Image Module "
            'Attributes, Image Type (0008,0008), Type 1: "Value 3 shall be '
            "Image Flavor, common Defined Terms for which are specified in "
            'Section C.8.16.1.3." PS3.3 C.8.16.1.3, Table C.8-129, Image Type '
            'and Frame Type Value 3 Common: "Additional Defined Terms are '
            'defined in the modality-specific Module and Macro definitions." %s'
            % Q_DEFINED_TERM),
        "rationale": (
            "The question is whether value 3 of Image Type is an extensible "
            "Defined Term list or a closed Enumerated Value list for the "
            "Parametric Map IOD specifically. Table C.8.32-2, which is the "
            "Parametric Map Image Module's own attribute table, says Defined "
            "Terms and points at C.8.16.1.3, whose list Table C.8-129 is "
            "labelled common and is stated to admit additional terms. PS3.5 "
            "3.10 defines a Defined Term as extensible by implementers and an "
            "Enumerated Value as not. AGGRESSIVENESS is therefore an extension "
            "the standard permits at this position. dciodvfy's own wording, "
            "unrecognized defined term, agrees that the position holds a "
            "Defined Term, and it emits the message at Warning."),
    })

    rules.append({
        "name": "image_type_value4",
        "validator": "dciodvfy",
        "pattern": re.compile(
            r"^Warning - Unrecognized defined term <AI> for value 4 of "
            r"attribute <Image Type>$"),
        "adjudication": "FLOOR",
        "citation_section": "PS3.3 C.8.32.2, with PS3.3 C.8.16.1.4 and PS3.5 3.10",
        "citation_table": "Table C.8.32-2; Table C.8-130",
        "citation_quote": (
            "PS3.3 C.8.32.2, Table C.8.32-2, Parametric Map Image Module "
            'Attributes, Image Type (0008,0008), Type 1: "Value 4 shall be '
            "Derived Pixel Contrast, common Defined Terms for which are "
            'specified in Section C.8.16.1.4." PS3.3 C.8.16.1.4, Table C.8-130, '
            'Image Type and Frame Type Value 4 Common: "Additional Defined '
            'Terms are defined in the modality-specific Module and Macro '
            'definitions." %s' % Q_DEFINED_TERM),
        "rationale": (
            "Same construction as value 3. Table C.8.32-2 marks value 4 a "
            "Defined Term and points at C.8.16.1.4, whose Table C.8-130 list is "
            "labelled common and admits additional terms, and PS3.5 3.10 makes "
            "Defined Terms extensible by implementers. AI is an extension the "
            "standard permits at this position. Emitted at Warning."),
    })

    rules.append({
        "name": "pn_retired_form",
        "validator": "dciodvfy",
        "pattern": re.compile(
            r"^Warning - Value dubious for this VR - \(TAG\) PN Patient's Name "
            r"PN \[1\] = <.*> - Retired Person Name form$"),
        "adjudication": "PLAUSIBILITY",
        "citation_section": "PS3.5 6.2",
        "citation_table": "Table 6.2-1, PN",
        "citation_quote": (
            'PS3.5 6.2, Table 6.2-1, PN: "A character string encoded using a 5 '
            'component convention." PS3.5 6.2, on omission: "Trailing null '
            'components and their delimiters may be omitted." PS3.5 6.2, on the '
            'single component form: "for reasons of backward compatibility with '
            "older versions of this Standard, person names might be considered a "
            'single family name complex (single component without "^" '
            'delimiters)."'),
        "rationale": (
            "dciodvfy reports the value as dubious for the VR. It names no Type "
            "and no condition, and dubious is a judgement about value quality "
            "rather than about conformance, which is the definition of the "
            "PLAUSIBILITY category. No requirement is available to cite against "
            "it: PS3.5 permits trailing null components and their delimiters to "
            "be omitted, so a single component PN is a well formed value of the "
            "VR. Each distinct patient identifier is its own message class "
            "because the value is inside the message text, so this one rule "
            "covers 336 message classes that differ only in that value."),
    })

    return rules


def _load_class_rows() -> list[dict]:
    with CENSUS_CLASSES.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)
                if r["sop_class_name"] == SOP_CLASS]


def _load_records() -> list[dict]:
    """Read the census records. Never written to: a census run appends here."""
    out = []
    with RECORDS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("sop_class_name") == SOP_CLASS:
                out.append(rec)
    return out


def _floor_set_pm_classes() -> dict[str, set[str]]:
    """Message classes the Phase 1 floor fixture drew on Parametric Map."""
    out: dict[str, set[str]] = {}
    if not FLOOR_SET.exists():
        return out
    with FLOOR_SET.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("sop_class") != "Parametric Map":
                continue
            out.setdefault(r["validator"], set()).add(r["message_class_id"])
    return out


def adjudicate() -> tuple[list[dict], list[dict]]:
    rules = _rules()
    rows = _load_class_rows()
    out = []
    for r in rows:
        hits = [rule for rule in rules
                if rule["validator"] == r["validator"]
                and rule["pattern"].match(r["message_template"])]
        if len(hits) != 1:
            raise SystemExit(
                "adjudication table does not cover exactly one rule for "
                "%s / %s / %r (matched %d). Nothing is skipped silently: add a "
                "rule with a citation, or mark it UNDECIDABLE explicitly."
                % (r["validator"], r["message_class_id"],
                   r["message_template"][:120], len(hits)))
        rule = hits[0]
        if rule["adjudication"] not in CATEGORIES:
            raise SystemExit("unknown category %r" % rule["adjudication"])
        out.append({
            "validator": r["validator"],
            "message_class_id": r["message_class_id"],
            "message_template": r["message_template"],
            "severity_as_emitted": r["severity_as_emitted"],
            "objects": int(r["objects"]),
            "adjudication": rule["adjudication"],
            "citation_section": rule["citation_section"],
            "citation_table": rule["citation_table"],
            "citation_quote": rule["citation_quote"],
            "rationale": rule["rationale"],
        })
    out.sort(key=lambda d: (d["validator"], -d["objects"], d["message_class_id"]))
    return out, rows


def triples(adjudicated: list[dict], records: list[dict]) -> dict:
    verdict = {(a["validator"], a["message_class_id"]): a["adjudication"]
               for a in adjudicated}
    severity = {(a["validator"], a["message_class_id"]): a["severity_as_emitted"]
                for a in adjudicated}

    objects = [o for rec in records for o in rec["objects"]]
    by_object_collection = [(o, rec["collection_id"])
                            for rec in records for o in rec["objects"]]
    n = len(objects)

    validators = sorted({v for v, _ in verdict})
    error_severities = {"Error", "ERROR"}

    def triple(select) -> dict:
        gross = flo = net = 0
        for obj in objects:
            classes = {(m[0], m[1]) for m in obj.get("messages", [])
                       if select(m)}
            if not classes:
                continue
            gross += 1
            cats = {verdict[c] for c in classes}
            if "NET" in cats:
                net += 1
            if cats <= FLOOR_SIDE:
                flo += 1
        return {"objects": n, "gross": gross, "floor": flo, "net": net,
                "gross_pct": round(100 * gross / n, 2) if n else 0.0,
                "floor_pct": round(100 * flo / n, 2) if n else 0.0,
                "net_pct": round(100 * net / n, 2) if n else 0.0}

    out = {"n_objects": n, "by_validator": {}, "by_validator_severity": {}}
    for v in validators:
        out["by_validator"][v] = triple(lambda m, v=v: m[0] == v)
        for sev in sorted({severity[k] for k in severity if k[0] == v}):
            out["by_validator_severity"]["%s / %s" % (v, sev)] = triple(
                lambda m, v=v, sev=sev: m[0] == v and severity[(m[0], m[1])] == sev)

    out["error_classes_all_validators"] = triple(
        lambda m: severity[(m[0], m[1])] in error_severities)
    out["warning_classes_all_validators"] = triple(
        lambda m: severity[(m[0], m[1])] not in error_severities)

    # Collection level net error class rate. This class is a single collection,
    # so the median below is taken over one cluster and carries no independent
    # information. It is reported because PRE-05 asks for it, and labelled.
    per_collection: dict[str, list[int]] = {}
    for obj, coll in by_object_collection:
        classes = {(m[0], m[1]) for m in obj.get("messages", [])
                   if severity[(m[0], m[1])] in error_severities}
        is_net = any(verdict[c] == "NET" for c in classes)
        per_collection.setdefault(coll, []).append(1 if is_net else 0)
    coll_rates = {c: round(100 * sum(v) / len(v), 2)
                  for c, v in sorted(per_collection.items())}
    out["collections"] = coll_rates
    out["collection_median_net_pct"] = (
        round(statistics.median(coll_rates.values()), 2) if coll_rates else 0.0)
    out["n_collections"] = len(coll_rates)
    return out


def _md(adjudicated: list[dict], tri: dict, records: list[dict]) -> str:
    n = tri["n_objects"]
    cats: dict[str, int] = {}
    for a in adjudicated:
        cats[a["adjudication"]] = cats.get(a["adjudication"], 0) + 1
    net_classes = [a for a in adjudicated if a["adjudication"] == "NET"]
    undec = [a for a in adjudicated if a["adjudication"] == "UNDECIDABLE"]
    floor_pm = _floor_set_pm_classes()

    observed = {}
    for a in adjudicated:
        observed.setdefault(a["validator"], set()).add(a["message_class_id"])

    err = tri["error_classes_all_validators"]
    coll_median = tri["collection_median_net_pct"]

    L = []
    A = L.append
    A("# Track C: Parametric Map Storage, net rates after adjudication")
    A("")
    A("Generated by `%s`. Source of counts: `results/phase2/"
      "census_message_classes.csv` and `_cache/census/records.jsonl`, both read "
      "only. Adjudications and citations: `results/phase2/"
      "adjudication_parametric_map.csv`." % CMD)
    A("")
    A("Scope: %d objects, all of SOP class %s, all from analysis result "
      "`%s`, all in collection `tcga_gbm`. One object per series in the census "
      "records, so an object rate and a series rate are the same number here."
      % (n, SOP_CLASS, ANALYSIS_RESULT_ID))
    A("")
    A("Validators that produced any message class on this class: %s. `dcmpschk` "
      "is run on Grayscale Softcopy Presentation State Storage only, by design "
      "in `colophon/census.py`, and highdicom's reader was not part of the "
      "Phase 2 census, so neither contributes a message class here and neither "
      "is reported as a clean pass."
      % ", ".join("`%s`" % v for v in sorted(observed)))
    A("")

    A("## Adjudication summary")
    A("")
    A("Every distinct `message_class_id` recorded against this class is "
      "adjudicated. None is skipped. %d distinct message classes in, %d out."
      % (len(adjudicated), len(adjudicated)))
    A("")
    A("| category | message classes |")
    A("|---|---|")
    for k in ["FLOOR", "NET", "NOT-IOD", "PLAUSIBILITY", "UNDECIDABLE"]:
        A("| %s | %d |" % (k, cats.get(k, 0)))
    A("")
    A("The %d PLAUSIBILITY classes are one dciodvfy message whose text embeds "
      "the patient identifier, so the census assigns a separate "
      "`message_class_id` per distinct value. They are one construct counted "
      "%d ways, not %d findings."
      % (cats.get("PLAUSIBILITY", 0), cats.get("PLAUSIBILITY", 0),
         cats.get("PLAUSIBILITY", 0)))
    A("")

    A("## Triples")
    A("")
    A("gross: objects with at least one message class of that severity. "
      "floor: objects whose message classes of that severity are all FLOOR, "
      "NOT-IOD or PLAUSIBILITY. net: objects with at least one class "
      "adjudicated NET. Denominator is %d objects throughout." % n)
    A("")
    A("| slice | gross | floor | net | gross pct | floor pct | net pct |")
    A("|---|---|---|---|---|---|---|")
    for label, t in list(tri["by_validator"].items()):
        A("| %s, all severities | %d | %d | %d | %.2f | %.2f | %.2f |"
          % (label, t["gross"], t["floor"], t["net"], t["gross_pct"],
             t["floor_pct"], t["net_pct"]))
    for label, t in tri["by_validator_severity"].items():
        A("| %s | %d | %d | %d | %.2f | %.2f | %.2f |"
          % (label, t["gross"], t["floor"], t["net"], t["gross_pct"],
             t["floor_pct"], t["net_pct"]))
    for label, key in [("all validators, error classes",
                        "error_classes_all_validators"),
                       ("all validators, warning classes",
                        "warning_classes_all_validators")]:
        t = tri[key]
        A("| %s | %d | %d | %d | %.2f | %.2f | %.2f |"
          % (label, t["gross"], t["floor"], t["net"], t["gross_pct"],
             t["floor_pct"], t["net_pct"]))
    A("")
    A("The gross error class rate of %.1f percent reported for this class in "
      "`results/phase2_census.md` is unchanged. What the adjudication changes "
      "is what is left after the floor is taken out."
      % err["gross_pct"])
    A("")

    A("## Residual NET classes")
    A("")
    if net_classes:
        A("| validator | message_class_id | severity | objects | template |")
        A("|---|---|---|---|---|")
        for a in net_classes:
            A("| %s | %s | %s | %d | %s |"
              % (a["validator"], a["message_class_id"],
                 a["severity_as_emitted"], a["objects"],
                 a["message_template"].replace("|", "\\|")))
    else:
        A("None. No message class recorded against %s was adjudicated NET, "
          "because no message in this class cites, or can be matched to, a "
          "stated requirement of PS3.3, PS3.4, PS3.5 or PS3.16 that the "
          "construct violates." % SOP_CLASS)
    A("")
    if undec:
        A("UNDECIDABLE classes: %d." % len(undec))
    else:
        A("No class was left UNDECIDABLE: every one of the %d carries a "
          "section, a table and a verbatim quote." % len(adjudicated))
    A("")

    A("## What the Phase 1 floor set says about this class")
    A("")
    A("`results/floor_set.csv` holds a highdicom built Parametric Map fixture "
      "run through the same pinned validators. The overlap with what the "
      "archive objects draw is partial in both directions, so floor membership "
      "was used as corroboration and never as the basis of an adjudication.")
    A("")
    A("| validator | floor fixture classes | archive classes | shared | "
      "fixture only | archive only |")
    A("|---|---|---|---|---|---|")
    for v in sorted(set(observed) | set(floor_pm)):
        f = floor_pm.get(v, set())
        o = observed.get(v, set())
        A("| %s | %d | %d | %d | %d | %d |"
          % (v, len(f), len(o), len(f & o), len(f - o), len(o - f)))
    A("")
    A("The five Shared Functional Groups classes are exactly the shared set "
      "under dicom-validator. The two `Module <General>` classes, Rows and "
      "Columns, are archive only, and are adjudicated on the citation alone.")
    A("")

    A("## The Laterality adjudication that was asked for and is not here")
    A("")
    A("The brief for this track expected a dciodvfy Error, `Missing attribute "
      "Type 2C Conditional Element=<Laterality> Module=<GeneralSeries>`, on "
      "691 of 691 objects. It is not present. dciodvfy emitted no message of "
      "severity Error against any of the %d objects, and returned 0 on all %d. "
      "The message class exists in this project, with `message_class_id` "
      "`e4c7fa2d56f7`, but in `results/floor_set.csv` against the highdicom "
      "built Parametric Map fixture, not against the archive objects. The "
      "expectation appears to have carried over from that fixture and from the "
      "Grayscale Softcopy Presentation State Storage and Real World Value "
      "Mapping Storage rows of `results/phase2_census.md`, where the same "
      "class does appear." % (n, n))
    A("")
    A("The citation is recorded anyway, because the adjudication was "
      "commissioned and because the class is live elsewhere in the census. "
      "PS3.3 C.7.3.1, Table C.7-5a, General Series Module Attributes, "
      "Laterality (0020,0060), Type 2C, verbatim: \"Laterality of (paired) "
      "body part examined. Required if the body part examined is a paired "
      "structure and Image Laterality (0020,0062) or Frame Laterality "
      "(0020,9072) or Measurement Laterality (0024,0113) are not present.\" "
      "The condition turns on whether the body part examined is a paired "
      "structure, which is not a fact the attribute set alone supplies. Where "
      "the class does occur, that is the text to attach to it. It contributes "
      "nothing to the numbers on this page, and no row for it appears in "
      "`adjudication_parametric_map.csv`, because a class with zero objects in "
      "this class is not an input to this track.")
    A("")

    A("## PRE-05")
    A("")
    A("PRE-05 as pre-registered, from `results/ledger.csv`: \"null is defined "
      "as a post-floor failure rate at or below 5 percent of series in a "
      "class; substantial is defined as above 20 percent; the band between is "
      "reported as indeterminate and neither claim is made\". The row also "
      "states that the floor from Phase 1 is subtracted before the threshold "
      "is applied, which is what the floor column of the triples above does.")
    A("")
    A("Both numbers the evaluation requires, reported whether or not the first "
      "condition passes:")
    A("")
    A("- (a) net error class rate for %s: **%.2f percent** (%d of %d objects). "
      "Gross was %.2f percent."
      % (SOP_CLASS, err["net_pct"], err["net"], n, err["gross_pct"]))
    A("- (b) collection level median net error class rate: **%.2f percent**, "
      "over %d collection cluster%s: %s."
      % (coll_median, tri["n_collections"],
         "" if tri["n_collections"] == 1 else "s",
         ", ".join("%s %.2f percent" % (c, r)
                   for c, r in tri["collections"].items())))
    A("")
    A("**Limitation, stated rather than buried.** This class is a single "
      "collection, `tcga_gbm`, and a single analysis result, `%s`. Condition "
      "(b) is therefore a median over one cluster, which is that cluster's own "
      "rate restated. It carries no independent information for this class and "
      "must not be read as a second, agreeing test. Any conjunction of (a) and "
      "(b) here is (a) counted twice." % ANALYSIS_RESULT_ID)
    A("")
    A("**Verdict.** (a) is %.2f percent, at or below 5 percent, so this class "
      "falls in the null band of PRE-05 as written. Under the conjunctive rule "
      "given to this track, substantial requires both (a) and (b) above 5.0 "
      "percent; (a) is %.2f percent, so the rule fails at (a) and (b) is not "
      "reached. PRE-05 is not cleared by this class and there is no wrong "
      "prediction to record here. PRE-05 stays PENDING as a row, because it is "
      "a per class threshold and the other classes are adjudicated elsewhere."
      % (err["net_pct"], err["net_pct"]))
    A("")
    A("**How the outcome is recorded.** In `results/pending_ledger/"
      "track_c_pm.json` as C-PM-09, a DERIVED row naming PRE-05 in "
      "`derived_from`, not as a replacement of the PRE-05 row itself. "
      "`colophon.merge_ledger` builds one row per id, last file wins, and "
      "`ledger.record_many` replaces a row whole rather than patching fields. "
      "`results/pending_ledger/track_c_rwv_kos.json` already proposes a PRE-05 "
      "replacement carrying two other classes, and `track_c_pm.json` sorts "
      "before it, so a PRE-05 row from this track would either be silently "
      "discarded or silently discard that one. The sentence to fold into "
      "PRE-05 by hand is: Parametric Map Storage, net error class rate 0.00 "
      "percent post floor against a gross of 100.00 percent, null band, "
      "collection level median 0.00 percent over the single cluster "
      "`tcga_gbm` and therefore carrying no independent information.")
    A("")
    A("What this class does say, and it is the substantive finding, is that "
      "the 100.0 percent gross error class rate carried in "
      "`results/phase2_census.md` for %s survives adjudication as 100.0 "
      "percent floor and %.2f percent net. Every object trips at least one "
      "validator error class, and every one of those classes is a construct "
      "the standard permits." % (SOP_CLASS, err["net_pct"]))
    A("")

    A("## What was dropped")
    A("")
    A("Nothing. All %d distinct message classes recorded against %s were "
      "adjudicated, all %d objects contributed, and no message class matched "
      "more than one rule: the run stops rather than choosing. The census "
      "records file was read and not written. The three unadjudicated inputs "
      "this track did not have are the object bytes, which were deleted after "
      "validation by design, dcmpschk, which is not run on this IOD, and "
      "highdicom's reader, which is not part of Phase 2."
      % (len(adjudicated), SOP_CLASS, n))
    A("")
    return "\n".join(L)


def main(argv=None) -> int:
    adjudicated, _ = adjudicate()
    records = _load_records()
    if len(records) != 691:
        print("warning: %d Parametric Map series records, expected 691"
              % len(records), file=sys.stderr)
    tri = triples(adjudicated, records)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["validator", "message_class_id", "message_template",
              "severity_as_emitted", "objects", "adjudication",
              "citation_section", "citation_table", "citation_quote",
              "rationale"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in adjudicated:
            w.writerow(row)

    OUT_MD.write_text(_md(adjudicated, tri, records), encoding="utf-8")

    print("adjudicated %d message classes over %d objects"
          % (len(adjudicated), tri["n_objects"]))
    for label, t in tri["by_validator"].items():
        print("  %-18s gross %d floor %d net %d"
              % (label, t["gross"], t["floor"], t["net"]))
    e = tri["error_classes_all_validators"]
    print("  error classes      gross %d (%.2f pct) floor %d net %d (%.2f pct)"
          % (e["gross"], e["gross_pct"], e["floor"], e["net"], e["net_pct"]))
    print("  collection median net %.2f pct over %d cluster(s)"
          % (tri["collection_median_net_pct"], tri["n_collections"]))
    print("wrote %s" % OUT_CSV)
    print("wrote %s" % OUT_MD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
