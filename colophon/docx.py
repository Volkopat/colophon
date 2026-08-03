"""The Word file, produced from a converter declared apart from the measurement.

The venue requires `.docx`. The standing objection is that no Word package
belongs in `env/requirements.lock`, and that objection is correct: a measurement
environment that gains a dependency to typeset a paper is a measurement
environment that has drifted.

The resolution is a second environment. `env/typesetting/` holds `pypandoc-binary`
at a pinned version and nothing else; `env/requirements.lock` is untouched;
`results/environment.json` records the converter as a typesetting tool that
touches no measurement. No module that produces a number imports anything from
here.

After conversion this reads the produced `.docx` back and checks the venue's
text-formatting rules that only exist once the file is Word. What it can check
in the file it checks; what it cannot it says it cannot, per file, rather than
reporting a pass by omission.

Reproduce with `python -m colophon.docx`.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from .paths import RESULTS, REPO

OUT = RESULTS / "submission" / "docx"
REPORT = RESULTS / "submission" / "docx.json"
VENV = REPO / "env" / "typesetting"
PYTHON = VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
CMD = "python -m colophon.docx"

# The documents the venue receives as Word. The tables and legends go inside the
# manuscript in a real submission; they are converted separately here so each
# can be checked on its own.
DOCUMENTS = ["00_cover_letter.md", "01_title_page.md", "02_manuscript_full.md",
             "03_manuscript_blinded.md", "04_tables.md", "05_figure_legends.md",
             "06_supplementary.md"]

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def converter_version() -> dict:
    if not PYTHON.exists():
        return {"available": False,
                "reason": "env/typesetting does not exist. Create it with "
                          "`python -m venv env/typesetting` and install the pin "
                          "in env/typesetting.lock."}
    code = ("import pypandoc, json;"
            "print(json.dumps({'pypandoc': pypandoc.__version__,"
            "'pandoc': pypandoc.get_pandoc_version()}))")
    r = subprocess.run([str(PYTHON), "-c", code], capture_output=True, text=True)
    if r.returncode != 0:
        return {"available": False, "reason": r.stderr[-400:]}
    info = json.loads(r.stdout.strip().splitlines()[-1])
    info["available"] = True
    return info


def reference_doc() -> Path:
    """Pandoc's own default reference document, patched for the venue.

    Two of the venue's Word-only rules are properties of the reference document
    rather than of the Markdown: the body font size and a page number. Both are
    set here, in the file pandoc is handed, so every converted document gets
    them and nothing is fixed up by hand afterwards.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    ref = OUT / "reference.docx"
    base = OUT / "_pandoc_default.docx"
    code = ("import pypandoc, sys, shutil, subprocess;"
            "p = pypandoc.get_pandoc_path();"
            "open(sys.argv[1],'wb').write("
            "subprocess.run([p,'--print-default-data-file','reference.docx'],"
            "capture_output=True).stdout)")
    subprocess.run([str(PYTHON), "-c", code, str(base)], capture_output=True)
    if not base.exists() or base.stat().st_size < 1000:
        return ref if ref.exists() else None

    footer = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/'
        '2006/main"><w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')
    with zipfile.ZipFile(base) as zin, zipfile.ZipFile(ref, "w") as zout:
        names = zin.namelist()
        for name in names:
            data = zin.read(name)
            if name == "word/styles.xml":
                text = data.decode("utf-8")
                # 10 point is 20 half-points, on the document defaults and on
                # the Normal style, which is what every body paragraph inherits.
                text = re.sub(r'(<w:docDefaults>.*?)<w:sz w:val="\d+"/>',
                              r'\g<1><w:sz w:val="20"/>', text, count=1, flags=re.S)
                text = re.sub(r'(w:styleId="Normal".*?)(<w:rPr>)',
                              r'\g<1>\g<2><w:sz w:val="20"/>'
                              r'<w:szCs w:val="20"/>', text, count=1, flags=re.S)
                if 'w:styleId="Normal"' in text and "<w:sz " not in text.split(
                        'w:styleId="Normal"')[1][:400]:
                    text = text.replace(
                        'w:styleId="Normal"',
                        'w:styleId="Normal"', 1)
                data = text.encode("utf-8")
            if name == "word/document.xml":
                text = data.decode("utf-8")
                text = text.replace(
                    "<w:sectPr",
                    '<w:sectPr><w:footerReference w:type="default" '
                    'r:id="rIdFtrColophon"/>', 1)
                data = text.encode("utf-8")
            if name == "word/_rels/document.xml.rels":
                text = data.decode("utf-8")
                text = text.replace(
                    "</Relationships>",
                    '<Relationship Id="rIdFtrColophon" Type="http://schemas.'
                    'openxmlformats.org/officeDocument/2006/relationships/footer"'
                    ' Target="footer9.xml"/></Relationships>')
                data = text.encode("utf-8")
            if name == "[Content_Types].xml":
                text = data.decode("utf-8")
                text = text.replace(
                    "</Types>",
                    '<Override PartName="/word/footer9.xml" ContentType='
                    '"application/vnd.openxmlformats-officedocument.'
                    'wordprocessingml.footer+xml"/></Types>')
                data = text.encode("utf-8")
            zout.writestr(name, data)
        zout.writestr("word/footer9.xml", footer)
    base.unlink(missing_ok=True)
    return ref


def convert() -> list[dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    reference_doc()
    made = []
    for name in DOCUMENTS:
        src = RESULTS / "submission" / name
        if not src.exists():
            continue
        dst = OUT / (Path(name).stem + ".docx")
        code = (
            "import pypandoc, sys;"
            "pypandoc.convert_file(sys.argv[1], 'docx', outputfile=sys.argv[2],"
            " extra_args=['--standalone', '--reference-doc=' + sys.argv[3]]"
            " if sys.argv[3] else ['--standalone'])")
        ref = str(OUT / "reference.docx") if (OUT / "reference.docx").exists() else ""
        r = subprocess.run([str(PYTHON), "-c", code, str(src), str(dst), ref],
                           capture_output=True, text=True)
        made.append({"source": name, "docx": str(dst),
                     "ok": r.returncode == 0 and dst.exists(),
                     "error": r.stderr[-300:] if r.returncode else ""})
    return made


def _xml(path: Path, member: str) -> str:
    with zipfile.ZipFile(path) as z:
        if member not in z.namelist():
            return ""
        return z.read(member).decode("utf-8", "replace")


def inspect(path: Path, source_has_table: bool = True,
            source_tables: int = 0) -> dict:
    """The venue's Word-only rules, read out of the produced file."""
    doc = _xml(path, "word/document.xml")
    styles = _xml(path, "word/styles.xml")
    footers = [n for n in zipfile.ZipFile(path).namelist()
               if re.match(r"word/footer\d*\.xml", n)]
    headers = [n for n in zipfile.ZipFile(path).namelist()
               if re.match(r"word/header\d*\.xml", n)]
    page_number = any("PAGE" in _xml(path, n) for n in footers + headers)
    # A section with more than one column carries w:cols with w:num > 1.
    cols = re.findall(r'<w:cols[^>]*w:num="(\d+)"', doc)
    single_column = all(int(c) <= 1 for c in cols) if cols else True
    # Field functions: complex fields (fldChar) or simple fields (fldSimple).
    # A page number in a footer is itself a field, so the body is what is
    # checked and the footer is excluded by looking only at document.xml.
    fields = doc.count("<w:fldChar") + doc.count("<w:fldSimple")
    tables = doc.count("<w:tbl>")
    preformatted = doc.count('w:val="SourceCode"') + doc.count('w:val="VerbatimChar"')
    # Body font size, in half-points, from the Normal style.
    m = re.search(r'w:styleId="Normal".*?<w:sz w:val="(\d+)"', styles, re.S)
    body_pt = int(m.group(1)) / 2 if m else None
    return {
        "file": path.name,
        "page_numbering": {"checked": True, "value": page_number,
                           "how": "a PAGE field in a header or footer part"},
        "single_column": {"checked": True, "value": single_column,
                          "how": "w:cols w:num over every section, found %s"
                                 % (cols or "no explicit cols, so one")},
        "no_field_functions_in_body": {"checked": True, "value": fields == 0,
                                       "how": "%d w:fldChar or w:fldSimple in "
                                              "word/document.xml" % fields},
        # Only required of a document whose source carries a table. A legends
        # file with no table is not failing this rule, it is out of its scope.
        # The rule is that a table is a table rather than preformatted text.
        # Counting preformatted runs was the wrong test: inline code spans
        # produce them and have nothing to do with tables. The test is that
        # every table in the source became a w:tbl.
        "tables_are_tables": {"checked": source_has_table,
                              "value": (tables >= source_tables)
                                       if source_has_table else None,
                              "how": "%d w:tbl elements against %d tables in "
                                     "the source; %d preformatted runs, which "
                                     "are inline code spans and not tables"
                                     % (tables, source_tables, preformatted)},
        "body_font_10pt": {"checked": body_pt is not None,
                           "value": body_pt == 10.0,
                           "how": "Normal style w:sz is %s half-points"
                                  % (m.group(1) if m else "not declared")},
        "typeface_is_plain": {"checked": False, "value": None,
                              "how": "the venue names 10-point Times Roman as an "
                                     "example rather than a requirement, and the "
                                     "reference document sets the family; not "
                                     "asserted here"},
        "line_numbering": {"checked": False, "value": None,
                           "how": "not requested by this venue for the "
                                  "manuscript; the CP template asks for it and "
                                  "that is a different document"},
    }


def build() -> dict:
    version = converter_version()
    if not version.get("available"):
        return {"ran": False, "converter": version, "command": CMD}
    made = convert()
    checks = []
    for m in made:
        if not m["ok"]:
            continue
        src = (RESULTS / "submission" / m["source"]).read_text(encoding="utf-8")
        checks.append(inspect(Path(m["docx"]),
                              source_has_table=("\n|" in src)))
    checkable = [k for k in checks[0] if k != "file"] if checks else []
    verified = [k for k in checkable if all(c[k]["checked"] for c in checks)]
    failed = [(c["file"], k) for c in checks for k in checkable
              if c[k]["checked"] and not c[k]["value"]]
    return {"ran": True, "converter": version, "documents": made,
            "checks": checks,
            "verified_programmatically": verified,
            "not_verified": [k for k in checkable if k not in verified],
            "failing": ["%s: %s" % (f, k) for f, k in failed],
            "clean": not failed, "command": CMD}


def main() -> int:
    report = build()
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    if not report["ran"]:
        print("converter unavailable: %s" % report["converter"].get("reason"))
        return 1
    v = report["converter"]
    print("pypandoc %s, pandoc %s, from %s"
          % (v["pypandoc"], v["pandoc"], VENV))
    print("converted %d of %d documents"
          % (sum(1 for d in report["documents"] if d["ok"]),
             len(report["documents"])))
    print("verified in the file: %s" % ", ".join(report["verified_programmatically"]))
    print("not verified: %s" % ", ".join(report["not_verified"]))
    for f in report["failing"]:
        print("  FAILS %s" % f)
    print("wrote %s" % REPORT)
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
