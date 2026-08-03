"""The pinning record.

Follows the Appendix E pattern in spine-gsps: every version string that could
change a number is captured next to the number. Tool binaries report their own
version where they have a flag, and their file fingerprint where they do not.
"""
from __future__ import annotations

import hashlib
import importlib.metadata as _md
import json
import platform
import subprocess
import sys
from pathlib import Path

from . import paths

PYTHON_PACKAGES = [
    "idc-index", "idc-index-data", "pandas", "duckdb", "pyarrow", "numpy",
    "s5cmd", "pydicom", "highdicom", "dicom-validator", "requests",
]


def _pkg(name: str) -> str:
    try:
        return _md.version(name)
    except Exception:
        return "not installed"


def _sha256(path: Path, limit: int = 1 << 26) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
            limit -= len(chunk)
            if limit <= 0:
                break
    return h.hexdigest()


def _binary(name: str) -> dict:
    path = getattr(paths, name.upper(), None)
    rec: dict = {"name": name, "path": str(path) if path else None}
    if path is None or not Path(path).exists():
        rec["status"] = "MISSING"
        return rec
    p = Path(path)
    rec["status"] = "present"
    rec["version_string"] = paths.binary_version(name)
    rec["size_bytes"] = p.stat().st_size
    rec["mtime_utc"] = __import__("datetime").datetime.utcfromtimestamp(
        p.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ")
    rec["sha256_first_64MiB"] = _sha256(p)
    return rec


def _hardware() -> dict:
    rec = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": sys.version.replace("\n", " "),
        "python_executable": sys.executable,
    }
    try:
        out = subprocess.run(
            ["wmic", "cpu", "get", "name"], capture_output=True, text=True, timeout=20)
        lines = [l.strip() for l in out.stdout.splitlines() if l.strip()]
        if len(lines) > 1:
            rec["cpu"] = lines[1]
    except Exception:
        pass
    try:
        import psutil  # bundled with idc-index
        rec["ram_GB"] = round(psutil.virtual_memory().total / (1024 ** 3), 1)
        rec["logical_cores"] = psutil.cpu_count(logical=True)
        rec["physical_cores"] = psutil.cpu_count(logical=False)
    except Exception:
        pass
    return rec


def snapshot(idc_version: str | None = None) -> dict:
    """Everything that has to be pinned, in one JSON-serialisable dict."""
    return {
        "idc_index_version": idc_version,
        "python_packages": {p: _pkg(p) for p in PYTHON_PACKAGES},
        "binaries": [_binary(b) for b in ("dciodvfy", "dcmpschk", "dcmdump", "dcmp2pgm")],
        "dicom3tools_snapshot": {
            "snapshot": "20260701065818",
            "package": "dicom3tools 1.00",
            "path": str(paths.DCIODVFY),
            "note": "dciodvfy exposes no version flag, so the snapshot is "
                    "carried forward from the spine-gsps environment record and "
                    "the binary itself is pinned by sha256 and mtime above. The "
                    "snapshot datestamp and the binary mtime agree to the day.",
        },
        "dicom_standard_edition": "PS3 2026c, dicom.nema.org. This is the edition dicom-validator downloaded and validated against, and the edition every PS3 citation in results/standards.json and the adjudications was checked against. An earlier value of 2025e here was stale and disagreed with both.",
        "hardware": _hardware(),
        "free_disk_GB_cache_volume": round(paths.free_gb(), 1),
    }


def write(path: Path | None = None, idc_version: str | None = None) -> Path:
    out = path or (paths.RESULTS / "environment.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot(idc_version), indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(snapshot(), indent=2))
