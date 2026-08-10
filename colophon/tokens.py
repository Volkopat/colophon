"""One substitution mechanism for everything the manuscript cannot state itself.

Three kinds of thing were being hand-typed into hand-written manuscript files:

- **a measured number in a disclosure**, which goes stale the moment the
  measurement is re-run;
- **a placeholder the author fills**, of which there were eighteen spread across
  four files, filled by editing generated output;
- **the status of the Correction Proposal**, which appears in three places and
  would need three edits the day it is filed.

All three are now tokens in the manuscript source, resolved when the submission
package is assembled. The manuscript source says where a value goes; this module
says what the value is; nothing is typed in two places.

Token forms:

    {{FIELD:key}}      from results/submission/fields.json, author-filled
    {{MEASURED:key}}   from a measurement artefact, computed
    {{CP_STATUS}}      the Correction Proposal status sentence, one source value

A `FIELD` that is still empty renders as a visible placeholder in a draft build
and **refuses** a final build. That is the whole point: the package cannot be
declared final while a field is unfilled, and filling one is editing a JSON
value rather than editing generated output.

Reproduce with `python -m colophon.tokens`.
"""
from __future__ import annotations

import json
import re

from .paths import RESULTS

FIELDS = RESULTS / "submission" / "fields.json"
CP_STATUS = RESULTS / "cp" / "status.json"
DISCLOSURE = RESULTS / "claim3" / "disclosure_search.json"

TOKEN = re.compile(r"\{\{(FIELD|MEASURED|CP_STATUS|CP_STATUS_SHORT)(?::([A-Za-z0-9_]+))?\}\}")
CMD = "python -m colophon.tokens"


class UnfilledField(Exception):
    """Raised when a final package is asked for and a field is still empty."""


# --- fields -------------------------------------------------------------------
def load_fields() -> dict:
    if not FIELDS.exists():
        return {}
    return json.loads(FIELDS.read_text(encoding="utf-8"))


def unfilled() -> list[str]:
    return sorted(k for k, v in load_fields().items()
                  if not str(v.get("value", "")).strip())


def field_value(key: str, final: bool) -> str:
    fields = load_fields()
    if key not in fields:
        raise KeyError("no field %r in %s. Add it there rather than typing a "
                       "value into a manuscript file." % (key, FIELDS))
    value = str(fields[key].get("value", "")).strip()
    if value:
        return value
    if final:
        raise UnfilledField(
            "field %r is empty and a final package was asked for. %s"
            % (key, fields[key].get("description", "")))
    return "`[FIELD %s: %s]`" % (key, fields[key].get("description", ""))


# --- measured -----------------------------------------------------------------
def measured(key: str) -> str:
    """A sentence computed from an artefact, never typed into the manuscript."""
    if key == "aycan_objects":
        from . import disclosure
        if not DISCLOSURE.exists():
            raise FileNotFoundError(
                "%s is missing. Run python -m colophon.disclosure" % DISCLOSURE)
        report = json.loads(DISCLOSURE.read_text(encoding="utf-8"))
        return disclosure.sentence(report)
    if key == "keywords":
        from . import submission
        return "; ".join(submission.KEYWORDS)
    if key == "abstract":
        from . import submission
        return submission.venue_abstract()
    if key == "aycan_attributes":
        report = json.loads(DISCLOSURE.read_text(encoding="utf-8"))
        searched = ", ".join("%s %s" % (a["name"], a["tag"])
                             for a in report["attributes_searched"])
        missing = ", ".join("%s %s" % (a["name"], a["tag"])
                            for a in report["attributes_not_captured_by_this_study"])
        return ("The attributes searched were %s. Two attributes named in the "
                "disclosure could not be searched, %s, because this study never "
                "read them into its records and the objects were deleted after "
                "validation" % (searched, missing))
    raise KeyError("no measured value %r" % key)


# --- correction proposal status ------------------------------------------------
STATES = {
    "drafted_not_filed": {
        "sentence": "This proposal is drafted and has not been filed at the "
                    "time of writing.",
        "short": "drafted and not filed",
    },
    "filed_awaiting_number": {
        "sentence": "This proposal was filed with the DICOM Secretariat on "
                    "{filed_on} and has not yet been assigned a number.",
        "short": "filed on {filed_on}, awaiting a number",
    },
    "assigned": {
        "sentence": "This proposal was filed with the DICOM Secretariat on "
                    "{filed_on} and is assigned {number}, status {status}.",
        "short": "filed on {filed_on}, {number}, status {status}",
    },
}


def cp_status() -> dict:
    if not CP_STATUS.exists():
        return {"state": "drafted_not_filed"}
    return json.loads(CP_STATUS.read_text(encoding="utf-8"))


def cp_sentence(short: bool = False) -> str:
    data = cp_status()
    state = data.get("state", "drafted_not_filed")
    if state not in STATES:
        raise ValueError("%s carries state %r, which is not one of %s"
                         % (CP_STATUS, state, sorted(STATES)))
    template = STATES[state]["short" if short else "sentence"]
    try:
        return template.format(**data)
    except KeyError as exc:
        raise ValueError("state %r needs %s in %s" % (state, exc, CP_STATUS))


# --- substitution ---------------------------------------------------------------
def resolve(text: str, final: bool = False) -> str:
    def sub(m):
        kind, key = m.group(1), m.group(2)
        if kind == "FIELD":
            return field_value(key, final)
        if kind == "MEASURED":
            return measured(key)
        if kind == "CP_STATUS":
            return cp_sentence()
        if kind == "CP_STATUS_SHORT":
            return cp_sentence(short=True)
        raise KeyError(kind)

    # A field value may itself name a field: `signature_block` is
    # "Digvijay Patil, {{FIELD:affiliation}}". A single substitution pass
    # inserted that value and stopped, so the marker shipped verbatim in the
    # cover letter signature while the field it named was filled. Substitute to
    # a fixed point, with a depth cap so a field that names itself fails loudly
    # rather than hanging the build.
    for _ in range(8):
        after = TOKEN.sub(sub, text)
        if after == text:
            return after
        text = after
    raise RecursionError(
        "a field value still contains a marker after 8 substitution passes, "
        "which means two fields name each other: %s"
        % sorted({m.group(0) for m in TOKEN.finditer(text)}))


def surviving_markers(text: str) -> list[str]:
    """Anything that still reads as a placeholder after a final build."""
    out = [m.group(0) for m in TOKEN.finditer(text)]
    out += re.findall(r"`\[FIELD[^`]*`", text)
    out += re.findall(r"`\[CONFIRM[^`]*`", text)
    return out


def main() -> int:
    fields = load_fields()
    empty = unfilled()
    print("fields: %d, unfilled %d" % (len(fields), len(empty)))
    for key in empty:
        print("  %-34s %s" % (key, fields[key].get("description", "")[:70]))
    print("correction proposal: %s" % cp_sentence(short=True))
    print("measured aycan clause: %s" % measured("aycan_objects"))
    return 0 if not empty else 1


if __name__ == "__main__":
    raise SystemExit(main())
