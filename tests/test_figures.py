"""The figures: reproducible, and carrying no number the ledger does not.

Three checks, matching the three QA steps. Regeneration must be byte-identical,
every annotated value must trace to a ledger row, and the rendering discipline
must hold across all six as one system. The third QA step, looking at the
rendered PNG, is not automatable and is not pretended to be here: text overflow,
collided labels and clipped legends were found by eye and the defects they
caught are recorded in the module docstring.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from colophon import figures, ledger

MANIFEST = figures.OUT / "manifest.json"


def _manifest() -> dict:
    """The six figures. Keys beginning with an underscore are reports about the
    set rather than members of it, and the contrast report is one."""
    if not MANIFEST.exists():
        pytest.skip("figures not drawn")
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def _report(key: str) -> dict:
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return raw.get(key, {})


def test_all_six_are_drawn_in_both_formats():
    m = _manifest()
    assert sorted(m) == ["figure%d" % n for n in range(1, 7)]
    for name, meta in m.items():
        for kind in ("pdf", "png"):
            p = Path(meta[kind])
            assert p.exists() and p.stat().st_size > 4000, (name, kind)


def test_regeneration_is_byte_identical():
    """QA step 1. A figure that changes on every run cannot be checked against
    anything, and a reviewer regenerating from a clean checkout must get what
    the paper shipped."""
    before = _manifest()
    rebuilt = {k: v for k, v in figures.build().items()
               if not k.startswith("_")}
    for name, meta in before.items():
        assert rebuilt[name]["sha256_pdf"] == meta["sha256_pdf"], (
            "%s is not reproducible" % name)


def test_every_annotated_value_is_in_the_ledger():
    """QA step 2. A figure carrying a number no ledger row carries fails."""
    m = _manifest()
    rows = {r["id"]: r for r in ledger.load()}
    for name, meta in m.items():
        cited = meta["ledger_rows"]
        assert cited, "%s cites no ledger row" % name
        blob = ""
        for rid in cited:
            assert rid in rows, "%s cites missing row %s" % (name, rid)
            r = rows[rid]
            blob += " ".join([r["value"], r["n"], r["denominator"],
                              r["status_note"], r["notes"], r["dropped"]])
        blob = blob.replace(",", "")
        for key, value in meta["annotated_values"].items():
            if not isinstance(value, (int, float)):
                continue
            token = ("%g" % value)
            assert token in blob.replace(".0 ", " "), (
                "%s annotates %s=%s, which none of %s carries"
                % (name, key, token, cited))


def test_every_figure_names_its_source_artefact():
    m = _manifest()
    for name, meta in m.items():
        src = Path(meta["source_artefact"])
        assert src.exists(), "%s draws from a missing artefact %s" % (name, src)
        assert meta["command"] == figures.CMD


def test_the_rendering_is_one_system():
    """Colour carries meaning or it is not used, and the palette is fixed."""
    source = Path(figures.__file__).read_text(encoding="utf-8")
    # No decorative colormaps beyond the single sequential one used for a
    # confusion matrix, and no gradients, 3D or shadows anywhere.
    for banned in ("viridis", "plasma", "rainbow", "jet", "Set1", "Set2",
                   "tab10", "tab20", "shadow=True", "projection='3d'",
                   "alpha=0.3, linewidth=3"):
        assert banned not in source, banned
    assert source.count("cmap=") <= 1
    # Every axis carries a unit or an explicit label.
    assert source.count("set_xlabel") + source.count("set_ylabel") >= 8
    assert figures.ACCENT and figures.GREY


def test_no_figure_ranks_producing_groups():
    """figures.md forbids a leaderboard, which is the one figure this study
    must not produce."""
    spec = (figures.RESULTS / "manuscript" / "figures.md").read_text(encoding="utf-8")
    assert "No leaderboard of producing groups" in spec
    source = Path(figures.__file__).read_text(encoding="utf-8")
    assert "sort_values(\"pct_informative\"" not in source
    assert "worst" not in source.lower()


def test_no_figure_draws_a_title_or_a_caption():
    """The venue's FIGURE LETTERING section: do not include titles or captions
    into your illustrations. All six carried a drawn-in title and figure 2
    carried a two-line caption along its bottom edge. The sentence is returned
    for the legend instead, and this checks the drawn object rather than the
    source, because a title can be set in more than one way."""
    figures.build()
    for n in sorted(figures.FIGURES):
        fig, values = figures.FIGURES[n]()
        drawn = [a.get_title(loc=w) for a in fig.axes
                 for w in ("left", "center", "right")]
        drawn += [t.get_text() for t in getattr(fig, "texts", [])]
        long_text = [s for s in drawn if len(str(s).strip()) > 3]
        figures.plt.close(fig)
        assert not long_text, (
            "figure %d draws %r, which belongs in the legend" % (n, long_text))
        assert values.get("_title"), (
            "figure %d draws no title and offers none for the legend" % n)


def test_every_lettering_pair_clears_the_contrast_minimum():
    """The venue asks for 4.5 to 1. Two pairings failed before this was
    computed: white on the medium grey at 1.98, and the light accent on white at
    3.54. The checklist row that used to cover this read `manual, not
    measured`."""
    figures.build()
    report = figures.contrast_report()
    assert report["pairs"], "nothing logged a text colour"
    assert report["clean"], "\n".join(
        "%s: %s on %s is %.2f:1" % (r["where"], r["fg"], r["bg"], r["ratio"])
        for r in report["failing"])
    assert report["lowest"]["ratio"] >= figures.MIN_CONTRAST


def test_figure_width_is_measured_off_the_shipped_file_not_the_canvas():
    """The drawing canvas is not the shipped width.

    This test used to compare `figsize` with the column width, which is the
    check that passed while figure 1 shipped 255 mm against a recorded 174. A
    tight bounding box grows to hold the lettering, so the only width that
    means anything is the one in the EPS, and the venue names four permitted
    values rather than a ceiling. The measurement lives in
    `colophon.assertions`; this asserts the two disagree, which is the fact
    that made the old test worthless.
    """
    from colophon import assertions
    result = assertions.figures_measured_from_the_shipped_file()
    assert result.passed, result.detail
    canvas = {}
    for n in sorted(figures.FIGURES):
        fig, _ = figures.FIGURES[n]()
        canvas[n] = round(fig.get_size_inches()[0] * 25.4, 1)
        figures.plt.close(fig)
    assert any(abs(canvas[n] - 174.0) > 1.0 for n in canvas), (
        "every canvas is the column width, so the distinction this test exists "
        "for is untestable and the test should be re-read rather than passed")


def test_the_contrast_guard_can_fail():
    """A guard that cannot fail is not a guard."""
    assert figures.contrast("#ffffff", "#b8b8b8") < figures.MIN_CONTRAST
    assert figures.contrast("#ffffff", "#1b4965") >= figures.MIN_CONTRAST
    assert figures.readable_on("#b8b8b8", "synthetic") == "#111111"
    assert figures.readable_on("#1b4965", "synthetic") == "#ffffff"


def test_figure3_uses_real_object_values():
    """The point of figure 3 is that the strings are precise, so a schematic
    placeholder would invert its meaning."""
    p = figures.OUT / "figure3_objects.json"
    if not p.exists():
        pytest.skip("figures not drawn")
    obj = json.loads(p.read_text(encoding="utf-8"))
    # Three exemplars, one per state of the finding. Two would assert the
    # headline without showing it, because both named exemplars name a producer.
    assert set(obj) == {"silent", "dcmqi", "highdicom"}
    for key, o in obj.items():
        assert o["Manufacturer"] and o["Model"] and o["SoftwareVersions"]
    # All three declare a non-MANUAL segment, so the Type 1C condition fires on
    # all three and the columns differ in what they say rather than in whether
    # they were asked to say anything. The earlier silent exemplar was entirely
    # MANUAL, which made its silence legitimate and not the paper's finding, and
    # ledger row FIG-02 records the swap.
    for key, o in obj.items():
        assert o["algtype"] != "MANUAL", key
        assert o["algname"], "%s satisfies the 1C condition with nothing" % key
    # Identity nowhere, with the condition satisfied by a value that names
    # nothing and the structured carrier beside it absent.
    assert obj["silent"]["ar"] == "rider_lungct_seg"
    assert obj["silent"]["algname"] == "0"
    assert obj["silent"]["ident"] == "absent"
    # Identity in the compelled free-text slot only.
    assert obj["dcmqi"]["algtype"] != "MANUAL"
    assert obj["dcmqi"]["ident"] == "absent"
    assert "TotalSegmentator" in obj["dcmqi"]["algname"]
    # Identity in the structured macro as well.
    assert obj["highdicom"]["ident"] == "present_complete"
    assert obj["highdicom"]["AlgorithmName"]
