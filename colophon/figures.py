"""The six figures, drawn from named artefacts and from nothing else.

Every value annotated on a figure is returned by the function that draws it and
checked against the ledger by `tests/test_figures.py`, so a figure cannot carry a
number the tables and the ledger do not.

**Rendering discipline, applied to all six as one system.**

Colour carries meaning. One accent for the thing the figure is about, grey for
everything it is compared against, and a second muted tone only where a figure
must separate two kinds of absence. No decorative palettes, no gradients, no
three-dimensional effects, no shadows.

Every axis carries its unit. Every denominator is in the caption rather than
implied. Where a figure shows a rate, the floor it is quoted against is on the
figure or in its caption.

One font at four sizes across all six. Vector PDF for typesetting and a 300 dpi
PNG for submission systems that demand raster.

Determinism: no random draw, no timestamp and no dictionary-order dependence
enters a figure, so regenerating from a clean checkout produces byte-identical
output. `tests/test_figures.py` regenerates and compares hashes.

Usage:
    python -m colophon.figures
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch, Rectangle

from .paths import RESULTS

CMD = "python -m colophon.figures"
# The output directory is overridable so that `colophon.reproducibility` can
# build the set twice, in two processes, into two directories and diff the
# bytes. A reproducibility claim checked inside one process is a claim about
# that process.
OUT = Path(os.environ.get("COLOPHON_FIGURES_OUT") or (RESULTS / "figures"))
CLAIM3 = RESULTS / "claim3"
ADJ2 = RESULTS / "adjudication2"
MANUSCRIPT = RESULTS / "manuscript"

# --- the one system -----------------------------------------------------------
ACCENT = "#1b4965"        # the thing the figure is about
ACCENT_LIGHT = "#5a8fa8"  # a second state of the same thing
GREY = "#b8b8b8"          # what it is compared against
GREY_DARK = "#6e6e6e"
RULE = "#333333"
HATCH_EDGE = "#8a8a8a"    # a fact that is structural rather than measured

FONT = "DejaVu Sans"
SIZE_TITLE, SIZE_LABEL, SIZE_TICK, SIZE_ANNOT = 11, 9.5, 8.5, 8

# The venue's single-column width, in inches. A figure drawn wider than this is
# scaled down in production, and the lettering goes down with it: figure 1 was
# drawn 193 mm wide, so its 8 pt labels printed at about 7.2 pt.
COLUMN_MM = 174.0
COLUMN_IN = COLUMN_MM / 25.4
MIN_CONTRAST = 4.5   # the venue's stated ratio for figure lettering
MIN_PT = 8.0         # the venue's stated 2 to 3 mm lettering, at print size


def relative_luminance(colour) -> float:
    """WCAG relative luminance, from a hex string or an RGB triple."""
    if isinstance(colour, str):
        h = colour.lstrip("#")
        rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    else:
        rgb = list(colour)[:3]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
           for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(fg, bg) -> float:
    a, b = relative_luminance(fg), relative_luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


# Every foreground-on-background pair used for text, logged as it is drawn, so
# the ratio is computed from what the figure actually does rather than asserted
# in a checklist. The check that used to read `manual, not measured` was the one
# manual item that was failing: white on GREY is 1.98:1 against a 4.5 minimum,
# and white on ACCENT_LIGHT is 3.54:1.
_CONTRAST_LOG: list[dict] = []


def _lettering(fg, bg, where: str):
    """Record a text-on-fill pair and return the foreground unchanged."""
    _CONTRAST_LOG.append({"where": where, "fg": str(fg), "bg": str(bg),
                          "ratio": round(contrast(fg, bg), 2)})
    return fg


def readable_on(bg, where: str, options=("#ffffff", "#111111")):
    """The option that reads on this background, logged with its ratio.

    A fixed rule such as `white if the cell is dark enough` fails in the middle
    of a sequential colormap, where neither white nor near-black is comfortable
    and the threshold picks the wrong one either side of it.
    """
    best = max(options, key=lambda fg: contrast(fg, bg))
    return _lettering(best, bg, where)


def contrast_report() -> dict:
    """What was logged on the last draw, lowest ratio first."""
    rows = sorted(_CONTRAST_LOG, key=lambda r: r["ratio"])
    failing = [r for r in rows if r["ratio"] < MIN_CONTRAST]
    return {"minimum_required": MIN_CONTRAST, "pairs": rows,
            "lowest": rows[0] if rows else None, "failing": failing,
            "clean": not failing}

plt.rcParams.update({
    "font.family": FONT,
    "font.size": SIZE_TICK,
    "axes.titlesize": SIZE_TITLE,
    "axes.labelsize": SIZE_LABEL,
    "xtick.labelsize": SIZE_TICK,
    "ytick.labelsize": SIZE_TICK,
    "legend.fontsize": SIZE_ANNOT,
    "axes.edgecolor": RULE,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 110,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03,
    "pdf.fonttype": 42,
    "svg.hashsalt": "colophon",
})


def _save(fig, name: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    pdf, png = OUT / ("%s.pdf" % name), OUT / ("%s.png" % name)
    # A creation timestamp in the PDF trailer would make the output differ on
    # every run and defeat the reproducibility check.
    fig.savefig(pdf, format="pdf", metadata={"CreationDate": None})
    fig.savefig(png, format="png", dpi=300)
    plt.close(fig)
    return {"pdf": str(pdf), "png": str(png),
            "sha256_pdf": hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]}


# --- Figure 1 -----------------------------------------------------------------
def figure1() -> tuple[plt.Figure, dict]:
    """Every one of the 31 cells labelled. 31 is few enough that binning them
    would hide the thing the figure exists to show."""
    src = CLAIM3 / "t33_recoverability_ladder.csv"
    d = pd.read_csv(src)
    d["lvl"] = d["first_level_identity_appears"].astype(str)
    order = {"none": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
    d["ord"] = d["lvl"].map(order)
    d = d.sort_values(["ord", "objects"], ascending=[True, False]).reset_index(drop=True)

    # Drawn at the column width rather than wider, so production does not scale
    # the lettering down below the venue's stated minimum. At 193 mm the 8 pt
    # labels printed at about 7.2 pt; at 174 mm they print at what they are.
    fig, ax = plt.subplots(figsize=(4.1, 10.4))
    y = np.arange(len(d))[::-1]
    for i, row in d.iterrows():
        appears = row["lvl"] != "none"
        fill = ACCENT if appears else GREY
        ax.barh(y[i], 1, color=fill, edgecolor="none", height=0.72)
        ax.text(0.5, y[i], row["lvl"] if appears else "none", ha="center",
                va="center", fontsize=MIN_PT, fontweight="bold",
                color=readable_on(fill, "figure1 in-bar level label"))
        if str(row["version_at_that_level"]).strip() == "yes":
            ax.text(1.06, y[i], "+ version", va="center", ha="left",
                    fontsize=MIN_PT, fontweight="bold",
                    color=_lettering(ACCENT, "#ffffff", "figure1 version flag"))
    ax.set_yticks(y)
    # The labels set the width. With a tight bounding box the canvas grows to
    # hold them, so the figure was shipping 255 mm wide against a 174 mm column
    # while the manifest recorded the 174 mm figsize as if it were a
    # measurement. The class is abbreviated and the word `objects` dropped.
    short = {"Grayscale Softcopy Presentation State": "GSPS",
             "Key Object Selection Document": "KOS",
             "Real World Value Mapping": "RWVM",
             "Comprehensive 3D SR": "C3D SR", "Comprehensive SR": "C SR",
             "RT Structure Set": "RTSTRUCT", "Parametric Map": "PMAP",
             "Segmentation": "SEG"}
    ax.set_yticklabels(["%s  %s  %s"
                        % (r.analysis_result_id[:22],
                           short.get(r.sop_class_name.replace(" Storage", ""),
                                     r.sop_class_name.replace(" Storage", "")),
                           format(int(r.objects), ","))
                        for r in d.itertuples()], fontsize=MIN_PT)
    _lettering("#000000", "#ffffff", "figure1 row labels")
    ax.set_xlim(0, 1.55)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("digit is the first carrier level at which producer identity "
                  "appears:\n1 equipment attributes, 2 file meta, 3 free text, "
                  "4 in-object algorithm carriers, 5 registry only",
                  fontsize=MIN_PT, labelpad=10)
    n_none = int((d["lvl"] == "none").sum())
    n_ver = int((d["version_at_that_level"] == "yes").sum())
    counts = d["lvl"].value_counts()
    # No title inside the illustration. The venue's FIGURE LETTERING section
    # says so in terms, and the sentence belongs in the legend, which already
    # carries it.
    # Above the axes, so it can never collide with the x-axis label below.
    ax.legend(handles=[Patch(facecolor=GREY, label="identity appears at no level"),
                       Patch(facecolor=ACCENT, label="identity appears")],
              loc="lower left", bbox_to_anchor=(0.0, 1.005), ncol=2,
              frameon=False, handlelength=1.4)
    return fig, {"cells": len(d), "none": n_none, "version": n_ver,
                 "level_1": int(counts.get("1", 0)), "level_3": int(counts.get("3", 0)),
                 "level_4": int(counts.get("4", 0)),
                 "_title": "Producer identity appears at no carrier level in "
                           "%d of %d analysis-result cells." % (n_none, len(d)),
                 "_source": str(src), "_ledger": ["C3T-03"]}


# --- Figure 2 -----------------------------------------------------------------
def figure2() -> tuple[plt.Figure, dict]:
    """The Type 1 binding is drawn as a strip below the axis, not as a bar.

    An earlier version drew "Type 1 does not bind" as a full-height hatched
    rectangle behind the non-conformant bar. It read as a 100 percent bar, which
    is the exact opposite of what it means, so the fact was moved into a
    register that cannot be mistaken for a value.
    """
    src = MANUSCRIPT / "table2.csv"
    d = pd.read_csv(src).sort_values("objects", ascending=False).reset_index(drop=True)
    binds = d["binds_provenance_type1"].astype(str).str.contains("yes")

    fig, (ax, axb) = plt.subplots(
        2, 1, figsize=(5.825, 5.0), sharex=True,
        gridspec_kw={"height_ratios": [11, 1], "hspace": 0.08})
    x = np.arange(len(d))
    w = 0.26
    for k, (col, colour) in enumerate([("non-conformant", ACCENT),
                                       ("conformant but uninformative", GREY),
                                       ("informative", ACCENT_LIGHT)]):
        ax.bar(x + (k - 1) * w, 100 * d[col] / d["objects"], w,
               color=colour, edgecolor="none")
    ax.set_ylabel("percent of objects in the class")
    ax.set_ylim(0, 108)
    ax.legend(handles=[Patch(facecolor=ACCENT, label="non-conformant"),
                       Patch(facecolor=GREY, label="conformant but uninformative"),
                       Patch(facecolor=ACCENT_LIGHT, label="informative")],
              loc="lower left", bbox_to_anchor=(0.0, 1.005), ncol=3,
              frameon=False, handlelength=1.4)

    for xi, can in enumerate(binds):
        axb.add_patch(Rectangle((xi - 0.34, 0.18), 0.68, 0.64,
                                facecolor=ACCENT if can else "white",
                                edgecolor=RULE if can else HATCH_EDGE,
                                hatch="" if can else "///", linewidth=0.7))
    axb.set_xlim(-0.6, len(d) - 0.4)
    axb.set_ylim(0, 1)
    axb.set_yticks([])
    for spine in axb.spines.values():
        spine.set_visible(False)
    axb.set_ylabel("Type 1\nbinds", rotation=0, ha="right", va="center",
                   fontsize=SIZE_ANNOT, labelpad=8)
    axb.set_xticks(x)
    axb.set_xticklabels([n.replace(" Storage", "")
                         .replace("Grayscale Softcopy Presentation State", "GSPS")
                         .replace("Key Object Selection Document", "KOS")
                         .replace("Real World Value Mapping", "RWVM")
                         .replace("Comprehensive 3D SR", "Comp 3D SR")
                         .replace("Comprehensive SR", "Comp SR")
                         .replace("RT Structure Set", "RTSTRUCT")
                         for n in d["sop_class_name"]], rotation=24, ha="right")
    # The two-line explanation that used to sit here, in figure coordinates
    # below the axes, was a caption baked into the illustration. It is the
    # legend's, and the legend carries it.
    _lettering("#000000", "#ffffff", "figure2 axis and tick labels")
    return fig, {"objects": int(d["objects"].sum()),
                 "iods_binding_type1": int(binds.sum()),
                 "iods_not_binding": int((~binds).sum()),
                 "_title": "Conformance and attribution are independent, and "
                           "the ceiling is the standard's.",
                 "_key": "Filled square: Enhanced General Equipment binds four "
                         "attributes at Type 1. Hatched square: it does not, so "
                         "absence of model, serial or software version is legal "
                         "there. Every class still binds Manufacturer at Type 2, "
                         "which is why KOS is non-conformant while its square is "
                         "unfilled.",
                 "_source": str(src), "_ledger": ["C3T-00", "STD-04", "STD-08"]}


# --- Figure 3 -----------------------------------------------------------------
def figure3() -> tuple[plt.Figure, dict]:
    """Two real objects, read from the Phase 3 records, values verbatim.

    The point of the figure is that the strings are precise, so a schematic
    placeholder would invert its meaning. An earlier version composed values
    from summary artefacts and inferred one of them; this reads both objects.
    """
    src = OUT / "figure3_objects.json"
    obj = json.loads(src.read_text(encoding="utf-8"))
    z, a, b = obj["silent"], obj["dcmqi"], obj["highdicom"]
    rows = [
        ("Manufacturer\n(0008,0070)",
         z["Manufacturer"], a["Manufacturer"], b["Manufacturer"], "equipment"),
        ("ManufacturerModelName\n(0008,1090)",
         z["Model"], a["Model"], b["Model"], "equipment"),
        ("SoftwareVersions\n(0018,1020)",
         z["SoftwareVersions"], a["SoftwareVersions"], b["SoftwareVersions"],
         "equipment"),
        ("ImplementationVersionName\n(0002,0013)",
         z["IVN"], a["IVN"], b["IVN"], "file meta"),
        ("SegmentAlgorithmType\n(0062,0008), Type 1",
         z["algtype"], a["algtype"], b["algtype"], "algorithm"),
        ("SegmentAlgorithmName\n(0062,0009), Type 1C",
         z["algname"], a["algname"], b["algname"], "algorithm"),
        ("SegmentationAlgorithm\nIdentificationSequence\n(0062,0007), Type 3",
         z["ident"], a["ident"], b["ident"], "algorithm"),
        ("  AlgorithmName in it\n  (0066,0036), Type 1",
         z["AlgorithmName"], a["AlgorithmName"], b["AlgorithmName"], "algorithm"),
    ]
    # At 366 mm this was drawn more than twice the column width, so production
    # would scale it to 48 percent and its 8 pt values would print at under
    # 4 pt. Drawn at the column width the old geometry collided: carrier labels
    # ran into the first value column, the analysis-result names overlapped each
    # other, and the rule key sat on top of a data row. The layout is rebuilt
    # for the width rather than squeezed into it.
    fig, ax = plt.subplots(figsize=(6.203, 7.4))
    ax.axis("off")
    xk, x0, x1, x2 = 0.0, 0.40, 0.615, 0.83
    top, step = 0.90, 0.093
    label_pt, value_pt = MIN_PT - 0.5, MIN_PT - 1.0
    ax.text(xk, top + 0.075, "carrier", fontsize=MIN_PT, fontweight="bold",
            color=_lettering(RULE, "#ffffff", "figure3 column heads"))
    heads = ((x0, "identity\nnowhere", z["ar"], GREY_DARK),
             (x1, "identity in the\ncompelled slot", a["ar"], ACCENT),
             (x2, "identity in the\nstructured macro", b["ar"], ACCENT))
    for x, w, ar, col in heads:
        ax.text(x, top + 0.085, w, fontsize=MIN_PT - 0.5, fontweight="bold",
                color=_lettering(col, "#ffffff", "figure3 column heads"),
                va="top", linespacing=1.3)
        # The analysis-result name is long and the columns are narrow, so it is
        # wrapped rather than allowed to run into its neighbour.
        wrapped = ar if len(ar) <= 18 else ar[:18] + "\n" + ar[18:36]
        ax.text(x, top + 0.017, wrapped, fontsize=value_pt - 0.5, va="top",
                family="monospace", linespacing=1.25,
                color=_lettering(GREY_DARK, "#ffffff", "figure3 analysis result"))

    gap = 0.05  # a band boundary, for the rule
    for i, (key, vz, va, vb, band) in enumerate(rows):
        y = top - 0.10 - i * step - (gap if band == "algorithm" else 0.0)
        ax.text(xk, y, key, fontsize=label_pt, va="center", linespacing=1.2,
                color=_lettering(RULE, "#ffffff", "figure3 carrier label"))
        for x, val in ((x0, vz), (x1, va), (x2, vb)):
            text = str(val) if str(val).strip() else "absent"
            absent = text in ("absent", "not written", "")
            # Truncate on a word boundary and mark it, so a clipped string is
            # never mistaken for the value the object actually carries.
            if len(text) > 17:
                cut = text[:17].rsplit(" ", 1)[0] if " " in text[:17] else text[:17]
                text = cut + "\u2026"
            ax.text(x, y, text, fontsize=value_pt, va="center",
                    family="monospace",
                    color=_lettering(GREY_DARK if absent else ACCENT, "#ffffff",
                                     "figure3 value"),
                    style="italic" if absent else "normal")
        if not (band == "algorithm" and rows[i - 1][3] != "algorithm"):
            ax.plot([xk, 1.0], [y - step / 2, y - step / 2],
                    color="#ececec", lw=0.6)
    # The rule sits between the file-meta band and the algorithm band, which is
    # where the standard stops compelling anything. Its key goes under the last
    # row, where nothing can collide with it.
    yline = top - 0.10 - 3 * step - step / 2 - gap * 0.45
    ax.plot([xk, 1.0], [yline, yline], color=RULE, lw=1.0)
    ybottom = top - 0.10 - len(rows) * step - gap - 0.04
    ax.text(xk, ybottom,
            "above the rule: compelled by the standard, and populated.\n"
            "below the rule: Type 3 or conditional, and the only place a "
            "producer is ever named",
            fontsize=label_pt, style="italic", va="top", linespacing=1.3,
            color=_lettering(GREY_DARK, "#ffffff", "figure3 rule key"))
    ax.set_xlim(-0.005, 1.005)
    ax.set_ylim(ybottom - 0.09, top + 0.135)
    return fig, {"dcmqi_sha": a["SoftwareVersions"],
                 "dcmqi_algorithm_name": a["algname"],
                 "highdicom_algorithm_name": b["AlgorithmName"],
                 "silent_algorithm_type": z["algtype"],
                 "silent_algorithm_name": z["algname"],
                 "_title": "All three record the serialiser exactly, and all "
                           "three declare a non-MANUAL segment, so all three "
                           "are compelled to supply a name. Supplying one is "
                           "not the same as identifying anything.",
                 "_source": str(src),
                 "_ledger": ["C3T-06", "DEV-02", "FIG-02", "P3-01", "P3-05"]}


# --- Figure 4 -----------------------------------------------------------------
def figure4() -> tuple[plt.Figure, dict]:
    """All 83 collections as points. The two masses are the finding, so binning
    them into bars would delete it."""
    src = CLAIM3 / "encoder_only_by_collection.csv"
    d = pd.read_csv(src).sort_values("pct").reset_index(drop=True)
    rng = np.random.default_rng(0)  # deterministic jitter, seeded
    jitter = rng.uniform(-0.30, 0.30, len(d))

    # 129 mm is unreachable for this one: its x-axis label alone
    # sets a tight-bounding-box floor near 142 mm, so it takes the
    # next permitted width up rather than a width off the grid.
    fig, ax = plt.subplots(figsize=(8.217, 3.3))
    at0, at100 = d["pct"] == 0, d["pct"] == 100
    between = ~(at0 | at100)
    for mask, colour, lab in ((at0, GREY, "0 percent"),
                              (at100, ACCENT, "100 percent"),
                              (between, ACCENT_LIGHT, "between")):
        ax.scatter(d.loc[mask, "pct"], jitter[mask.values], s=34, color=colour,
                   edgecolor="white", linewidth=0.5, zorder=3, label=lab)
    # Without a boundary a reader counting grey dots cannot reach 44, because
    # jittered "between" points near 0 sit visually inside the mass at 0.
    for edge in (2.0, 98.0):
        ax.axvline(edge, color="#dcdcdc", lw=0.9, zorder=1)
    ax.set_yticks([])
    ax.set_ylim(-0.70, 0.68)
    ax.set_xlim(-4, 104)
    ax.set_xlabel("percent of a collection's objects whose equipment attributes "
                  "name only an encoder")
    ax.spines["left"].set_visible(False)
    n0, n100, nb = int(at0.sum()), int(at100.sum()), int(between.sum())
    for xpos, n in ((0, n0), (100, n100)):
        ax.text(xpos, 0.50, "%d collections" % n, ha="center",
                fontsize=MIN_PT, fontweight="bold",
                color=_lettering(GREY_DARK if xpos == 0 else ACCENT, "#ffffff",
                                 "figure4 mass label"))
    # ACCENT_LIGHT reads at 3.54:1 on white and is a fill colour, not a text
    # colour. The label takes the dark accent and the point it labels keeps the
    # light one, so the tie between them is position rather than hue.
    ax.text(50, -0.52, "%d collections between" % nb, ha="center",
            fontsize=MIN_PT, fontweight="bold",
            color=_lettering(ACCENT, "#ffffff", "figure4 between label"))
    return fig, {"collections": int(len(d)), "at_zero": n0, "at_hundred": n100,
                 "between": nb,
                 "_title": "Two point masses, not a spread: why no median is "
                           "reported for these distributions.",
                 "_source": str(src), "_ledger": ["C3T-02"]}


# --- Figure 5 -----------------------------------------------------------------
def figure5() -> tuple[plt.Figure, dict]:
    """Two lines on one axis. V9 is marked with its reason, because the value
    alone invites the reader to think the floor moved when the tool failed."""
    src = RESULTS / "phase1_variants.csv"
    v = pd.read_csv(src)
    v = v[(v["sop_class"] == "SEG BINARY") & v["message_class_id"].notna()]
    # V0 is the baseline and V0R is the round-trip control. Neither is a rung.
    rungs = sorted(r for r in v["variant"].unique() if r not in ("V0", "V0R"))
    out = {}
    for validator in ("dciodvfy", "dicom-validator"):
        jac, res = [], []
        for rung in rungs:
            sub = v[(v["variant"] == rung) & (v["validator"] == validator)]
            sets = {w: set(g["message_class_id"]) for w, g in sub.groupby("writer")}
            a, b = sets.get("highdicom", set()), sets.get("dcmqi", set())
            union = a | b
            jac.append(len(a & b) / len(union) if union else float("nan"))
            res.append(len(a ^ b))
        out[validator] = (jac, res)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.942, 3.6), sharex=True)
    x = np.arange(len(rungs))
    ax1.plot(x, out["dciodvfy"][0], marker="o", ms=4, color=GREY, label="dciodvfy")
    ax1.plot(x, out["dicom-validator"][0], marker="s", ms=4, color=GREY_DARK,
             ls="--", label="dicom-validator")
    ax1.set_ylabel("Jaccard between the two\nwriters' floor sets", fontsize=MIN_PT)
    ax1.set_ylim(-0.05, 1.18)
    # Panel letters, not descriptive panel titles. The descriptive pair said
    # "unstable under dciodvfy, stable under dicom-validator" on the left while
    # the figure title said the Jaccard is "not stable under either reading",
    # which read as a contradiction on one image. What each panel shows is the
    # legend's to say.
    ax1.set_title("a", loc="left", fontsize=SIZE_LABEL, fontweight="bold",
                  color=_lettering(RULE, "#ffffff", "figure5 panel letter"))
    ax2.plot(x, out["dciodvfy"][1], marker="o", ms=4, color=ACCENT, label="dciodvfy")
    ax2.plot(x, out["dicom-validator"][1], marker="s", ms=4, color=ACCENT_LIGHT,
             ls="--", label="dicom-validator")
    ax2.set_ylabel("residue: message classes\nheld by one writer only",
                   fontsize=MIN_PT)
    ax2.set_ylim(0, 3.4)
    ax2.set_yticks([0, 1, 2, 3])
    ax2.set_title("b", loc="left", fontsize=SIZE_LABEL, fontweight="bold",
                  color=RULE)
    if "V9" in rungs:
        i9 = rungs.index("V9")
        ax2.annotate("V9: the pinned dciodvfy build cannot read\n"
                     "the deflated transfer syntax, so this rung\n"
                     "is adjudicated UNDECIDABLE",
                     xy=(i9, out["dciodvfy"][1][i9]), xytext=(0.30, 2.62),
                     fontsize=SIZE_ANNOT, color=RULE,
                     arrowprops=dict(arrowstyle="->", color=RULE, lw=0.7,
                                     connectionstyle="arc3,rad=-0.18"))
    for ax in (ax1, ax2):
        ax.set_xticks(x)
        ax.set_xticklabels(rungs, fontsize=SIZE_TICK)
        ax.set_xlabel("variant rung")
        ax.legend(frameon=False, loc="lower left", fontsize=MIN_PT, ncol=2,
                  bbox_to_anchor=(0.0, -0.40))
    _lettering("#000000", "#ffffff", "figure5 axis and tick labels")
    fig.subplots_adjust(top=0.90, bottom=0.30, wspace=0.42)
    return fig, {"rungs": len(rungs),
                 "residue_dicom_validator_max": int(max(out["dicom-validator"][1])),
                 "residue_dciodvfy_max": int(max(out["dciodvfy"][1])),
                 "_title": "The residue is the stable quantity. The Jaccard is "
                           "not: it oscillates under one validator and holds "
                           "under the other, so its value depends on which tool "
                           "is asked.",
                 "_source": str(src), "_ledger": ["B-02", "B-03", "B-05", "B-10"]}


# --- Figure 6 -----------------------------------------------------------------
def figure6() -> tuple[plt.Figure, dict]:
    """The 147 pre-disclosed classes are drawn beside the matrix and labelled
    excluded, so the exclusion is visible rather than stated in a caption."""
    src = ADJ2 / "two_pass_comparison.csv"
    d = pd.read_csv(src)
    agree = json.loads((ADJ2 / "agreement.json").read_text(encoding="utf-8"))
    blind = d[~d["pre_disclosed"].astype(bool)]
    m = np.zeros((2, 2), dtype=int)
    for i, p1 in enumerate([True, False]):
        for j, p2 in enumerate([True, False]):
            m[i, j] = int(((blind["net1"].astype(bool) == p1)
                           & (blind["net2"].astype(bool) == p2)).sum())

    fig, (ax, axr) = plt.subplots(1, 2, figsize=(7.491, 3.4),
                                  gridspec_kw={"width_ratios": [2.6, 1]})
    cmap = plt.get_cmap("Blues")
    ax.imshow(m, cmap=cmap, vmin=0, vmax=m.max())
    for i in range(2):
        for j in range(2):
            # The cell's own colour decides the text colour. The rule this
            # replaces used a fixed threshold on the value, which put white on
            # a mid-blue cell at about 3:1.
            cell = cmap(m[i, j] / m.max() if m.max() else 0.0)
            ax.text(j, i, format(int(m[i, j]), ","), ha="center", va="center",
                    fontsize=SIZE_LABEL, fontweight="bold",
                    color=readable_on(cell, "figure6 matrix cell"))
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["counts toward net", "does not"])
    ax.set_yticklabels(["counts toward net", "does not"])
    ax.set_xlabel("pass 2"); ax.set_ylabel("pass 1")
    ax.set_title("a", loc="left", fontsize=SIZE_LABEL, fontweight="bold",
                 color=_lettering(RULE, "#ffffff", "figure6 panel letter"))
    for s in ("top", "right"):
        ax.spines[s].set_visible(True)

    n_pre = int(d["pre_disclosed"].astype(bool).sum())
    axr.bar([0], [n_pre], width=0.5, color=GREY, edgecolor="none", hatch="///")
    axr.set_xticks([0]); axr.set_xticklabels(["pre-disclosed"])
    axr.set_ylabel("message classes")
    axr.set_ylim(0, max(n_pre * 1.75, 10))
    axr.text(0, n_pre * 1.12, "%d classes\nEXCLUDED from\nthe matrix" % n_pre,
             ha="center", fontsize=MIN_PT, fontweight="bold",
             color=_lettering(RULE, "#ffffff", "figure6 exclusion label"))
    axr.set_title("b", loc="left", fontsize=SIZE_LABEL, fontweight="bold",
                  color=RULE)
    fig.subplots_adjust(top=0.90, wspace=0.42)
    return fig, {"blind_classes": int(agree["net_binary_blind"]["n"]),
                 "kappa": agree["net_binary_blind"]["kappa"],
                 "agreement": agree["net_binary_blind"]["agreement"],
                 "pre_disclosed": n_pre,
                 "total_classes": int(agree["message_classes"]),
                 "_title": "Two adjudication passes agree on the decision that "
                           "reaches a rate. This is an intra-instrument check. "
                           "a, the blind subset of %s message classes, "
                           "agreement %s percent, Cohen's kappa %s. b, the %d "
                           "pre-disclosed classes, excluded from the matrix."
                           % (format(agree["net_binary_blind"]["n"], ","),
                              agree["net_binary_blind"]["agreement"],
                              agree["net_binary_blind"]["kappa"], n_pre),
                 "_source": str(src), "_ledger": ["ADJ2-01", "ADJ2-02"]}


# Numbered by where each is first cited in the body, which is what the venue
# asks of tables and asks of figures in the same sentence. The builders keep
# their old names; only the numbers move. Content order in the text runs the
# ladder, the grades, the mechanism, the floors, the adjudication and then the
# two camps, so the floor figure is 4, the adjudication figure is 5 and the
# collection-mass figure is 6.
FIGURES = {1: figure1, 2: figure2, 3: figure3,
           4: figure5, 5: figure6, 6: figure4}


def _write_figure3_objects() -> Path:
    """One dcmqi object and one highdicom object, read from the Phase 3 records.

    Published as its own artefact so the figure draws from a file a reader can
    open, and so the values in it are not recomposed on every run.
    """
    from . import phase3
    # Three exemplars, one per state of the finding: identity nowhere, identity
    # in the compelled free-text slot only, identity in the structured macro.
    #
    # The silent exemplar was `dicom_lidc_idri_nodules`, every segment of which
    # declares MANUAL. That is legitimate silence: the Type 1C condition never
    # fires, so nothing was omitted and nothing was avoided, and it is not the
    # case the paper is about. `rider_lungct_seg` is, and the check that found
    # it is `colophon.silent_column`, ledger row FIG-02. Its segments declare
    # AUTOMATIC, so the condition fires, a name is compelled, a name is
    # supplied, and the name is the single character 0.
    want = {"rider_lungct_seg": "silent",
            "totalsegmentator_ct_segmentations": "dcmqi",
            "tcga_sbu_til_maps": "highdicom"}
    found = {}
    for record in phase3.load_records():
        key = want.get(record.get("analysis_result_id"))
        if not key or key in found:
            continue
        for o in record.get("objects", []):
            if o.get("status") != "OK":
                continue
            segments = o.get("segments", [])
            if not segments:
                continue
            # All three exemplars are drawn from a non-MANUAL segment, so all
            # three are objects the condition actually applies to and the three
            # columns differ only in what they say, never in whether they were
            # asked to say anything.
            segs = [x for x in segments if x.get("non_manual")]
            if not segs:
                continue
            seg = segs[0]
            macro = (seg.get("macro") or [{}])[0]
            found[key] = {
                "ar": record["analysis_result_id"],
                "Manufacturer": o.get("Manufacturer", ""),
                "Model": o.get("ManufacturerModelName", ""),
                "SoftwareVersions": o.get("SoftwareVersions", ""),
                "IVN": o.get("ImplementationVersionName", ""),
                "algtype": seg.get("SegmentAlgorithmType", "") or "absent",
                "ident": seg["identification"],
                "algname": seg.get("SegmentAlgorithmName", "") or "",
                "AlgorithmName": macro.get("AlgorithmName_value", ""),
                "AlgorithmVersion": macro.get("AlgorithmVersion_value", ""),
            }
            break
        if len(found) == 3:
            break
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "figure3_objects.json"
    path.write_text(json.dumps(found, indent=2, sort_keys=True), encoding="utf-8")
    return path


def build() -> dict:
    _write_figure3_objects()
    _CONTRAST_LOG.clear()
    manifest = {}
    for n in sorted(FIGURES):
        fig, values = FIGURES[n]()
        files = _save(fig, "figure%d" % n)
        manifest["figure%d" % n] = {
            "source_artefact": values.pop("_source"),
            "ledger_rows": values.pop("_ledger"),
            "command": CMD,
            # The sentence that used to be drawn into the illustration. The
            # venue forbids a title inside a figure, so it is carried here and
            # printed by the legend builder instead of by matplotlib.
            "title_for_the_legend": values.pop("_title", ""),
            "key_for_the_legend": values.pop("_key", ""),
            "annotated_values": values,
            **files,
        }
    manifest["_contrast"] = contrast_report()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                       encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    manifest = build()
    for name, meta in manifest.items():
        if name.startswith("_"):
            continue
        print("%-9s %s  sha %s" % (name, Path(meta["pdf"]).name,
                                   meta["sha256_pdf"]))
        print("          values: %s" % meta["annotated_values"])
    report = manifest["_contrast"]
    lowest = report["lowest"]
    print("contrast: %d text pairs, lowest %.2f:1 (%s), minimum required %.1f:1"
          % (len(report["pairs"]), lowest["ratio"], lowest["where"],
             report["minimum_required"]))
    for row in report["failing"]:
        print("  FAILS: %s %s on %s at %.2f:1"
              % (row["where"], row["fg"], row["bg"], row["ratio"]))
    print("wrote %s" % (OUT / "manifest.json"))
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
