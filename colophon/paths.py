"""Single source of truth for where things live.

Same pattern as spine-gsps `src/spinelab/paths.py`. Every large artifact sits
outside the repository. Override any entry with an environment variable of the
same name.

The validator binaries are deliberately the ones the spine-gsps paper used. A
different build of dciodvfy or DCMTK reports different diagnostics, which would
make cross-phase and cross-paper comparison meaningless. If a binary is missing
this module says so and the caller stops. It never falls back to PATH.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# The spine-gsps project root, which owns the pinned third party toolchain.
SPINE_ROOT = Path(os.environ.get("COLOPHON_SPINE_ROOT", r"D:\Radiology\Spine Labeling"))
SPINE_REPO = Path(os.environ.get("COLOPHON_SPINE_REPO", str(SPINE_ROOT / "spine-gsps")))
TOOLS = Path(os.environ.get("COLOPHON_TOOLS", str(SPINE_ROOT / "tools")))

# --- third party validators, pinned -----------------------------------------
DCIODVFY = Path(os.environ.get(
    "COLOPHON_DCIODVFY", str(TOOLS / "dicom3tools" / "dciodvfy.exe")))
DCMTK_BIN = Path(os.environ.get(
    "COLOPHON_DCMTK_BIN", str(TOOLS / "dcmtk" / "dcmtk-3.7.0-win64-dynamic" / "bin")))
DCMPSCHK = DCMTK_BIN / "dcmpschk.exe"
DCMDUMP = DCMTK_BIN / "dcmdump.exe"
DCMP2PGM = DCMTK_BIN / "dcmp2pgm.exe"
DSRDUMP = DCMTK_BIN / "dsrdump.exe"

# --- reference implementations, the second measurement axis -------------------
# These are not validators. They are the readers that consuming software would
# actually use, and a refusal to parse is evidence of a different kind from a
# validator complaint. dcmqi ships them inside the 3D Slicer tree in the pinned
# toolchain. The standalone dcmqi 1.5.6 release is also present as an unopened
# archive; the installed 1.5.4 build is pinned because it is the one that runs
# today. Override with COLOPHON_DCMQI_BIN to change that, and re-pin.
DCMQI_BIN = Path(os.environ.get(
    "COLOPHON_DCMQI_BIN",
    str(TOOLS / "viewers" / "slicer" / "lib" / "Python" / "Lib" /
        "site-packages" / "dcmqi" / "bin")))
SEGIMAGE2ITKIMAGE = DCMQI_BIN / "segimage2itkimage.exe"
TID1500READER = DCMQI_BIN / "tid1500reader.exe"
PARAMAP2ITKIMAGE = DCMQI_BIN / "paramap2itkimage.exe"

# PixelMed DicomSRValidator. The IDC team validates its own SR with this, so an
# audit of IDC SR that omits it uses a weaker instrument than its subject.
JAVA = Path(os.environ.get(
    "COLOPHON_JAVA",
    str(TOOLS / "viewers" / "jre" / "jdk-17.0.20+8-jre" / "bin" / "java.exe")))
PIXELMED_JAR = Path(os.environ.get(
    "COLOPHON_PIXELMED_JAR", str(TOOLS / "pixelmed" / "pixelmed.jar")))

# --- in repo, committed ------------------------------------------------------
RESULTS = REPO / "results"
PHASE0 = RESULTS / "phase0"
FIGURES = RESULTS / "figures"
LEDGER = RESULTS / "ledger.csv"
ENV = REPO / "env"

# --- outside the repo, never committed ---------------------------------------
# Fetched DICOM lands here and is deleted after validation rather than kept.
CACHE = Path(os.environ.get("COLOPHON_CACHE", str(REPO / "_cache")))

_BINARIES = {
    "dciodvfy": DCIODVFY,
    "dcmpschk": DCMPSCHK,
    "dcmdump": DCMDUMP,
    "dcmp2pgm": DCMP2PGM,
    "dsrdump": DSRDUMP,
    "segimage2itkimage": SEGIMAGE2ITKIMAGE,
    "tid1500reader": TID1500READER,
    "paramap2itkimage": PARAMAP2ITKIMAGE,
    "java": JAVA,
    "pixelmed_jar": PIXELMED_JAR,
}


def require(path: Path, what: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(
            "%s not found at %s. This is a pinned binary. Do not substitute "
            "another build: set the matching COLOPHON_* variable or stop." % (what, path))
    return path


def binary_version(name: str) -> str:
    """Report a binary's own version string, for the pinning appendix.

    dciodvfy has no version flag. dicom3tools carries its snapshot date in the
    distribution directory name and in the executable, so we report what the
    binary itself prints plus the file's modification time, and the caller
    records the snapshot separately.
    """
    path = _BINARIES.get(name)
    if path is None or not path.exists():
        return "MISSING"
    for flag in ("--version", "-version"):
        try:
            proc = subprocess.run([str(path), flag], capture_output=True,
                                  text=True, errors="replace", timeout=30)
        except Exception:
            continue
        for line in (proc.stdout + proc.stderr).strip().splitlines():
            # Only tools that actually self-report are accepted. Anything else
            # is the tool complaining about the flag, and reporting that as a
            # version string would put a sentence like "unrecognized option"
            # into the pinning appendix.
            if "$dcmtk:" in line or "repository URL" in line:
                return line.strip()
            if line.lower().startswith(("openjdk version", "java version")):
                return line.strip()
    return "no version flag, pinned by sha256 and mtime"


def describe() -> str:
    rows = [
        ("REPO", REPO), ("SPINE_ROOT", SPINE_ROOT), ("SPINE_REPO", SPINE_REPO),
        ("TOOLS", TOOLS), ("DCIODVFY", DCIODVFY), ("DCMPSCHK", DCMPSCHK),
        ("DCMDUMP", DCMDUMP), ("DCMP2PGM", DCMP2PGM), ("DSRDUMP", DSRDUMP),
        ("SEGIMAGE2ITK", SEGIMAGE2ITKIMAGE), ("TID1500READER", TID1500READER),
        ("PARAMAP2ITK", PARAMAP2ITKIMAGE), ("JAVA", JAVA),
        ("PIXELMED_JAR", PIXELMED_JAR),
        ("RESULTS", RESULTS), ("CACHE", CACHE),
    ]
    out = []
    for name, p in rows:
        out.append("  %-12s %-72s %s" % (name, p, "ok" if p.exists() else "MISSING"))
    return "\n".join(out)


def free_gb(path: Path | None = None) -> float:
    """Free space in GB on the volume holding `path`. Called before every fetch."""
    target = path or CACHE
    probe = target
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    return shutil.disk_usage(probe).free / (1024 ** 3)


if __name__ == "__main__":
    print(describe())
    print("\n  free on cache volume: %.1f GB" % free_gb())
    for name in _BINARIES:
        print("  %-10s %s" % (name, binary_version(name)))
