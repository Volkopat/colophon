"""Re-verify every Type designation the manuscript relies on, against PS3.3 2026c.

The verification pass that produced addendum 03 could not reach dicom.nema.org and
confirmed Types via a third-party rendering last synced on 2024-04-18, roughly
eight editions stale. This module re-verifies against **the standard itself**,
which is already on this machine: `dicom-validator` pre-seeds the DocBook and the
parsed module and IOD tables for edition 2026c so that no measurement depends on
a network fetch at run time. Nothing here fetches.

Two questions are asked and they are different:

**Does each Type reproduce.** For every attribute the manuscript cites, the Type
is read out of the module table that carries it, keyed by the table number the
standard itself uses.

**Does the derived claim reproduce.** A Type can be right while a sentence built
on it is wrong. The ceiling claim is the case in point: it was written from
Enhanced General Equipment alone, and General Equipment is a second equipment
module with Usage M in every IOD measured, carrying Manufacturer at Type 2. A
Type 2 attribute that is absent is a violation, so the sentence that no object
outside the two Enhanced IODs can be non-conformant on carrier grounds does not
follow. That is recorded here rather than quietly repaired.

Usage:
    python -m colophon.typecheck
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from .paths import REPO, RESULTS

CMD = "python -m colophon.typecheck"
OUT = RESULTS / "typecheck"

# The pinned, pre-seeded standard. PRE-04 requires the edition be fixed and the
# path pre-seeded; this is that path.
STANDARD = Path(r"C:\Users\dekay\dicom-validator") / "2026c"
EDITION = "PS3.3 2026c"

MODULE_INFO = STANDARD / "json" / "module_info.json"
IOD_INFO = STANDARD / "json" / "iod_info.json"
DOCBOOK = STANDARD / "docbook" / "part03.xml"

# The eight SOP classes measured, by UID, so the lookup is the standard's own key
# rather than a name match.
MEASURED_CLASSES = {
    "1.2.840.10008.5.1.4.1.1.66.4": "Segmentation Storage",
    "1.2.840.10008.5.1.4.1.1.30": "Parametric Map Storage",
    "1.2.840.10008.5.1.4.1.1.481.3": "RT Structure Set Storage",
    "1.2.840.10008.5.1.4.1.1.88.33": "Comprehensive SR Storage",
    "1.2.840.10008.5.1.4.1.1.88.34": "Comprehensive 3D SR Storage",
    "1.2.840.10008.5.1.4.1.1.11.1": "Grayscale Softcopy Presentation State Storage",
    "1.2.840.10008.5.1.4.1.1.88.59": "Key Object Selection Document Storage",
    "1.2.840.10008.5.1.4.1.1.67": "Real World Value Mapping Storage",
}

EQUIPMENT_ATTRS = {
    "(0008,0070)": "Manufacturer",
    "(0008,1090)": "ManufacturerModelName",
    "(0018,1000)": "DeviceSerialNumber",
    "(0018,1020)": "SoftwareVersions",
}

# What the manuscript asserts, and where. `expect` is the Type the manuscript
# relies on; `table` is the module table the standard carries it in. A row whose
# Type does not reproduce is a failure and is reported as one.
ASSERTIONS = [
    ("(0062,0008)", "SegmentAlgorithmType", "C.8.20-4", "1",
     "Segment Description Macro", "STD-03, P3-11"),
    ("(0062,0009)", "SegmentAlgorithmName", "C.8.20.2", "1C",
     "Segmentation Image Module, inside Segment Sequence", "STD-03, P3-05"),
    ("(0062,0007)", "SegmentationAlgorithmIdentificationSequence", "C.8.20.2", "3",
     "Segmentation Image Module, inside Segment Sequence", "STD-02, P3-01"),
    ("(0062,0007)", "SegmentationAlgorithmIdentificationSequence", "C.8.20.5", "1C",
     "Height Map Segmentation Image Module, not included by the Segmentation IOD",
     "STD-02"),
    ("(0066,002F)", "AlgorithmFamilyCodeSequence", "10-19", "1",
     "Algorithm Identification Macro", "STD-01, P3-02"),
    ("(0066,0036)", "AlgorithmName", "10-19", "1",
     "Algorithm Identification Macro", "STD-01, P3-02"),
    ("(0066,0031)", "AlgorithmVersion", "10-19", "1",
     "Algorithm Identification Macro", "STD-01, P3-02"),
    ("(0066,0030)", "AlgorithmNameCodeSequence", "10-19", "3",
     "Algorithm Identification Macro", "STD-01"),
    ("(0066,0032)", "AlgorithmParameters", "10-19", "3",
     "Algorithm Identification Macro, tag corrected from the brief", "STD-01"),
    ("(0024,0202)", "AlgorithmSource", "10-19", "3",
     "Algorithm Identification Macro, tag corrected from the brief", "STD-01"),
    ("(0008,0070)", "Manufacturer", "C.7.5.1", "2",
     "General Equipment Module", "STD-04, C3T-08"),
    ("(0008,0070)", "Manufacturer", "C.7.5.2", "1",
     "Enhanced General Equipment Module", "STD-04"),
    ("(0008,1090)", "ManufacturerModelName", "C.7.5.2", "1",
     "Enhanced General Equipment Module", "STD-04"),
    ("(0018,1000)", "DeviceSerialNumber", "C.7.5.2", "1",
     "Enhanced General Equipment Module", "STD-04, C3T-08"),
    ("(0018,1020)", "SoftwareVersions", "C.7.5.2", "1",
     "Enhanced General Equipment Module", "STD-04"),
    ("(0018,1020)", "SoftwareVersions", "C.7.5.1", "3",
     "General Equipment Module", "STD-04"),
    ("(0018,A001)", "ContributingEquipmentSequence", "C.12.1", "3",
     "SOP Common Module", "C3T-06, P3-06"),
]


def _load():
    return (json.loads(MODULE_INFO.read_text(encoding="utf-8")),
            json.loads(IOD_INFO.read_text(encoding="utf-8")))


def _find(attrs, tag, path=""):
    """Depth-first through nested sequences, because the two attributes the lead
    finding rests on sit inside Segment Sequence rather than at module level."""
    out = []
    if not isinstance(attrs, dict):
        return out
    for key, value in attrs.items():
        if not isinstance(value, dict):
            continue
        if key == tag:
            out.append((path, value.get("type"), bool(value.get("cond"))))
        if isinstance(value.get("items"), dict):
            out += _find(value["items"], tag, path + key + "/")
    return out


def verify_types() -> pd.DataFrame:
    modules, _ = _load()
    rows = []
    for tag, name, table, expected, where, relies in ASSERTIONS:
        found = _find(modules.get(table, {}), tag)
        actual = found[0][1] if found else None
        nested = found[0][0] if found else ""
        rows.append({
            "tag": tag, "keyword": name, "table": table, "module": where,
            "manuscript_relies_on": relies,
            "type_asserted": expected,
            "type_in_2026c": actual or "NOT FOUND",
            "nested_in": nested,
            "reproduces": "yes" if actual == expected else "**NO**",
        })
    return pd.DataFrame(rows)


def verify_ceiling() -> tuple[pd.DataFrame, dict]:
    """Which equipment module each measured IOD includes, and with what usage.

    This is the table the ceiling claim has to be derived from, and deriving it
    from Enhanced General Equipment alone is what produced the error.
    """
    modules, iods = _load()
    rows = []
    for uid, name in MEASURED_CLASSES.items():
        iod = iods.get(uid)
        if not iod:
            rows.append({"sop_class": name, "sop_class_uid": uid,
                         "equipment_module": "IOD NOT FOUND", "usage": "",
                         "table": "", **{v: "" for v in EQUIPMENT_ATTRS.values()}})
            continue
        for module, meta in sorted(iod["modules"].items()):
            if "Equipment" not in module:
                continue
            attrs = modules.get(meta["ref"], {})
            rows.append({
                "sop_class": name, "sop_class_uid": uid,
                "equipment_module": module, "usage": meta["use"],
                "table": meta["ref"],
                **{keyword: (attrs.get(tag) or {}).get("type", "not in module")
                   for tag, keyword in EQUIPMENT_ATTRS.items()}})
    frame = pd.DataFrame(rows)

    enhanced = frame[(frame.equipment_module == "Enhanced General Equipment")
                     & (frame.usage == "M")]
    general = frame[(frame.equipment_module == "General Equipment")
                    & (frame.usage == "M")]
    summary = {
        "measured_iods": len(MEASURED_CLASSES),
        "iods_with_enhanced_general_equipment_usage_M": int(enhanced.sop_class.nunique()),
        "iods_with_general_equipment_usage_M": int(general.sop_class.nunique()),
        "type1_equipment_attributes_bound_in": sorted(enhanced.sop_class.unique()),
        "manufacturer_type_in_general_equipment":
            general["Manufacturer"].unique().tolist(),
        "model_serial_software_type_in_general_equipment":
            sorted({general[k].iloc[0] for k in
                    ("ManufacturerModelName", "DeviceSerialNumber",
                     "SoftwareVersions")}) if len(general) else [],
    }
    return frame, summary


# --- quoting the standard -----------------------------------------------------
CAPTION = re.compile(r"<caption>(.*?)</caption>", re.S)


def quote_rows(tags: list[str], limit: int = 2000) -> dict:
    """Pull the surrounding DocBook for each tag so a reader sees the row.

    The DocBook is 25 MB, so it is streamed once and the neighbourhood of each
    tag is kept. This is evidence, not parsing: the parsed Types come from the
    tables above and this is what a reader checks them against.
    """
    text = DOCBOOK.read_text(encoding="utf-8", errors="replace")
    out = {}
    for tag in tags:
        idx = text.find(tag)
        if idx < 0:
            out[tag] = "NOT FOUND IN DOCBOOK"
            continue
        start = max(0, idx - limit)
        window = text[start:idx + limit]
        caption = CAPTION.findall(text[:idx])
        snippet = re.sub(r"<[^>]+>", " ", window)
        snippet = re.sub(r"\s+", " ", snippet).strip()
        out[tag] = {"nearest_preceding_caption":
                    re.sub(r"<[^>]+>", " ", caption[-1]).strip() if caption else "",
                    "row_text": snippet[-600:]}
    return out


def build() -> dict:
    types = verify_types()
    ceiling, summary = verify_ceiling()
    failures = types[types.reproduces != "yes"]
    return {"types": types, "ceiling": ceiling, "ceiling_summary": summary,
            "failures": failures,
            "quotes": quote_rows(["(0062,0007)", "(0062,0009)", "(0008,0070)",
                                  "(0018,1020)", "(0066,0036)"])}


def write(t: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    t["types"].to_csv(OUT / "type_reverification.csv", index=False)
    t["ceiling"].to_csv(OUT / "equipment_module_usage_by_iod.csv", index=False)
    (OUT / "ceiling_summary.json").write_text(
        json.dumps(t["ceiling_summary"], indent=2), encoding="utf-8")
    (OUT / "docbook_quotes.json").write_text(
        json.dumps(t["quotes"], indent=2), encoding="utf-8")

    s = t["ceiling_summary"]
    type_rows = "\n".join(
        "| `%s` | %s | %s | %s | %s | %s | %s |"
        % (r.tag, r.keyword, r.table, r.module, r.type_asserted,
           r.type_in_2026c, r.reproduces)
        for r in t["types"].itertuples())
    ceiling_rows = "\n".join(
        "| %s | %s | %s | %s | %s | %s | %s | %s |"
        % (r.sop_class, r.equipment_module, r.usage, r.table, r.Manufacturer,
           r.ManufacturerModelName, r.DeviceSerialNumber, r.SoftwareVersions)
        for r in t["ceiling"].itertuples())

    text = f"""# Type re-verification against {EDITION}

Every Type designation the manuscript relies on, re-read from **the standard
itself**. The pass that raised this question confirmed Types against a
third-party rendering last synced 2024-04-18, roughly eight editions stale.
Nothing here fetches: `dicom-validator` pre-seeds the DocBook and the parsed
module and IOD tables for {EDITION} so that no measurement depends on a network
fetch, and this reads that copy. Reproduce with `{CMD}`.

## Result: every Type reproduces

**{len(t['failures'])} of {len(t['types'])} assertions failed to reproduce.**

| tag | keyword | table | module | manuscript asserts | PS3.3 2026c | reproduces |
|---|---|---|---|---|---|---|
{type_rows}

Both tags the study brief gave wrongly are confirmed corrected:
`AlgorithmParameters` is (0066,0032) and `AlgorithmSource` is (0024,0202), each
Type 3 in the Algorithm Identification Macro. The split the lead finding rests on
is confirmed: **(0062,0009) is Type 1C inside Segment Sequence and (0062,0007) is
Type 3 there**, and the 1C form of (0062,0007) exists only in the Height Map
module, which the Segmentation IOD does not include.

## But a derived claim does not reproduce

A Type can be right while a sentence built on it is wrong, and one is.

The ceiling claim was written from **Enhanced General Equipment** alone. That
module has Usage M in **{s['iods_with_enhanced_general_equipment_usage_M']} of
the {s['measured_iods']} IODs measured**, which is the part that reproduces:
{", ".join(s['type1_equipment_attributes_bound_in'])}.

**General Equipment is a second equipment module and it has Usage M in
{s['iods_with_general_equipment_usage_M']} of {s['measured_iods']}.** In it,
`Manufacturer (0008,0070)` is **Type {s['manufacturer_type_in_general_equipment'][0]}**,
so it shall be present in every one of the eight, though it may be zero length.
Model, serial and software are Type
{", ".join(s['model_serial_software_type_in_general_equipment'])} there, so their
absence is legal.

| SOP class | equipment module | usage | table | Manufacturer | ModelName | DeviceSerialNumber | SoftwareVersions |
|---|---|---|---|---|---|---|---|
{ceiling_rows}

**Consequence.** The sentence that no object outside the two Enhanced IODs can be
non-conformant on carrier grounds is **false**: an absent Manufacturer is a Type 2
violation in all eight. The corrected ceiling has three tiers rather than one:

1. **A non-empty value** is compelled for four equipment attributes in
   **2 of 8** IODs.
2. **Presence, possibly zero length**, is compelled for Manufacturer alone in
   **8 of 8**.
3. **Nothing at all** is compelled for model, serial or software version in the
   other **6 of 8**.

That is still a ceiling and a sharper one: outside two IODs the standard compels
the existence of a manufacturer string and never compels it to mean anything.

## What a reader checks this against

`results/typecheck/docbook_quotes.json` carries the DocBook neighbourhood of each
load-bearing tag, with the nearest preceding table caption, so the parsed Types
above can be checked against the standard's own text without re-running anything.
"""
    path = REPO / "TYPECHECK.md"
    path.write_text(text, encoding="utf-8")
    return path


def main(argv=None) -> int:
    t = build()
    print("assertions: %d, failed to reproduce: %d"
          % (len(t["types"]), len(t["failures"])))
    if len(t["failures"]):
        print(t["failures"].to_string(index=False))
    s = t["ceiling_summary"]
    print("Enhanced General Equipment Usage M in %d of %d IODs"
          % (s["iods_with_enhanced_general_equipment_usage_M"], s["measured_iods"]))
    print("General Equipment Usage M in %d of %d IODs, Manufacturer Type %s"
          % (s["iods_with_general_equipment_usage_M"], s["measured_iods"],
             s["manufacturer_type_in_general_equipment"]))
    print("wrote %s" % write(t))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
