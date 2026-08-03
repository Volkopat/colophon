"""Is any object in the measured set written by the disclosed company.

The competing-interests block asserted that "nothing of that company's appears
anywhere in this study", which bundles three different claims into one hedge:
where the work was done, when the employment ran, and whether any object in the
measured set came from that company. The first two are the author's to state.
The third is measurable and was being asserted.

This measures the third. It searches the equipment and description attributes of
every object in the writer census that backs Table 1, case-insensitively, for the
company string as a substring, and reports the count by SOP class and the
distinct values matched.

**Two of the seven attributes the disclosure names are not captured by this
study at all.** `InstitutionName (0008,0080)` and `StationName (0008,1010)` were
never read into the census records, and the objects were deleted after
validation, so they cannot be searched without re-fetching. That is reported
here and in the disclosure rather than left for a reader to assume the search
covered seven attributes when it covered five and a sequence.

Reproduce with `python -m colophon.disclosure`.
"""
from __future__ import annotations

import collections
import json

from .paths import RESULTS

OUT = RESULTS / "claim3" / "disclosure_search.json"
CMD = "python -m colophon.disclosure"

# The company named in the competing-interests block. Lowercase throughout, per
# the house rule, and matched case-insensitively so a capitalised spelling in an
# object would still be found.
COMPANY = "aycan"

# The attributes the disclosure names. `captured` says whether this study ever
# read the attribute into its records; an attribute that was never read cannot
# be searched and is not counted as searched.
ATTRIBUTES = [
    ("Manufacturer", "(0008,0070)", True),
    ("ManufacturerModelName", "(0008,1090)", True),
    ("SoftwareVersions", "(0018,1020)", True),
    ("DeviceSerialNumber", "(0018,1000)", True),
    ("InstitutionName", "(0008,0080)", False),
    ("StationName", "(0008,1010)", False),
    ("SeriesDescription", "(0008,103E)", True),
]
# Not in the seven, but it is the carrier the study itself treats as equipment
# identity, so leaving it out would be a gap the disclosure could hide in.
SEQUENCE = "ContributingEquipmentSequence"


def _sequence_values(obj: dict) -> list[str]:
    out = []
    for item in obj.get("ContributingEquipmentSequence_items") or []:
        if isinstance(item, dict):
            out += [str(v) for v in item.values() if v]
        else:
            out.append(str(item))
    return out


def search(company: str = COMPANY) -> dict:
    from . import census, phase3
    needle = company.lower()
    searched = [name for name, _tag, captured in ATTRIBUTES if captured]
    not_captured = [(name, tag) for name, tag, captured in ATTRIBUTES
                    if not captured]

    objects = 0
    by_class = collections.Counter()
    hits = collections.Counter()
    matched_values = collections.Counter()
    per_attribute = collections.Counter()
    for loader, fallback in ((phase3.load_records, "Segmentation Storage"),
                             (census.load_records, None)):
        for record in loader():
            if record.get("status") != "OK":
                continue
            for obj in record.get("objects", []) or []:
                if obj.get("status") != "OK":
                    continue
                objects += 1
                sop = (fallback or obj.get("sop_class_name")
                       or record.get("sop_class_name") or "unknown")
                by_class[sop] += 1
                found = False
                for name in searched:
                    value = str(obj.get(name, "") or "")
                    if needle in value.lower():
                        per_attribute[name] += 1
                        matched_values[value] += 1
                        found = True
                for value in _sequence_values(obj):
                    if needle in value.lower():
                        per_attribute[SEQUENCE] += 1
                        matched_values[value] += 1
                        found = True
                if found:
                    hits[sop] += 1

    return {
        "company": company,
        "match": "case-insensitive substring",
        "objects_searched": objects,
        "objects_in_the_measured_set": sum(
            v for k, v in by_class.items() if k != "Enhanced SR Storage"),
        "unit": "objects, one row per SOP instance read",
        "objects_by_sop_class": dict(sorted(by_class.items())),
        "attributes_searched": [
            {"name": n, "tag": t} for n, t, c in ATTRIBUTES if c
        ] + [{"name": SEQUENCE, "tag": "(0018,A001)",
              "note": "every value of every item, added because it is the "
                      "carrier this study treats as equipment identity"}],
        "attributes_not_captured_by_this_study": [
            {"name": n, "tag": t,
             "reason": "never read into the census or Phase 3 records, and the "
                       "objects were deleted after validation, so it cannot be "
                       "searched without re-fetching"}
            for n, t in not_captured],
        "matching_objects": int(sum(hits.values())),
        "matching_objects_by_sop_class": dict(sorted(hits.items())),
        "distinct_values_matched": len(matched_values),
        "values_matched": dict(matched_values.most_common(20)),
        "matches_per_attribute": dict(per_attribute.most_common()),
        "command": CMD,
    }


def sentence(report: dict) -> str:
    """The measured clause, in the shape the disclosure uses."""
    n = report["matching_objects"]
    searched = len(report["attributes_searched"])
    total = "{:,}".format(report["objects_searched"])
    named = len(ATTRIBUTES)
    captured = sum(1 for _n, _t, c in ATTRIBUTES if c)
    if n == 0:
        measured_set = report.get("objects_in_the_measured_set", 0)
        return ("no object in the measured set is written by that company: %d "
                "matching objects out of %s objects searched, a superset that "
                "contains all %s objects of the measured set and the %s "
                "Enhanced SR objects excluded from every rate. The search was a "
                "case-insensitive substring match over %d of the %d equipment "
                "and description attributes named in this disclosure, plus "
                "every value of every item of ContributingEquipmentSequence "
                "(0018,A001) (DISC-01)"
                % (n, total, "{:,}".format(measured_set),
                   "{:,}".format(report["objects_searched"] - measured_set),
                   captured, named))
    return ("%d of %s objects in the measured set match that company in an "
            "equipment or description attribute" % (n, total))


def main() -> int:
    report = search()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print("searched %s objects for %r over %d attributes"
          % ("{:,}".format(report["objects_searched"]), report["company"],
             len(report["attributes_searched"])))
    print("  matching objects: %d" % report["matching_objects"])
    if report["matching_objects"]:
        print("  by class: %s" % report["matching_objects_by_sop_class"])
        print("  distinct values: %d" % report["distinct_values_matched"])
    print("  not captured by this study, so not searched: %s"
          % ", ".join("%s %s" % (a["name"], a["tag"])
                      for a in report["attributes_not_captured_by_this_study"]))
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
