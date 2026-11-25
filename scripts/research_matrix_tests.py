#!/usr/bin/env python3
"""CLI-level regression tests for the research-matrix skill's scripts.

    python3 scripts/research_matrix_tests.py

Each check runs the real command-line scripts on small fixtures in a temp
folder: APA 7 order and initials, formula-injection and control-character
safety, id/DOI keying that survives renumbering, validation errors, the
Crossref check (markup, DOI case, retraction notices, a misspelt surname) and
the Scimago year logic. Exits non-zero if any check fails.
"""
import glob
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SK = str(Path(__file__).resolve().parent.parent / "skills" / "research-matrix")
SC = SK + "/scripts"
EX = SK + "/examples"
# LibreOffice recalculation from the xlsx skill, if installed (set RECALC to override).
_rc = os.environ.get("RECALC") or next(iter(glob.glob(os.path.expanduser("~/.claude/skills/**/xlsx/scripts/recalc.py"), recursive=True)), None)
RECALC = _rc
T = tempfile.mkdtemp(prefix="rm-test-")
RESULTS = []


def run(script, *args):
    p = subprocess.run([sys.executable, "-I", f"{SC}/{script}", *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def ok(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if (detail and not cond) else ""))


def wj(name, obj):
    path = f"{T}/{name}"
    json.dump(obj, open(path, "w"), ensure_ascii=False)
    return path


def paper(authors, year, title, **kw):
    d = {"authors": authors, "year": year, "title": title, "journal": "J Test", "volume": "1", "pages": "1-2",
         "type": "Quantitative", "access": "Free", "quartile": "Unranked/Unavailable"}
    d.update(kw)
    return d


import openpyxl  # noqa: E402

# ---- APA / sort / suffix / DOI
sys.path.insert(0, SC)
import common as C  # noqa: E402
ok("initials hyphen", C.initials("J.-P.") == "J.-P.")
ok("initials bare AJ", C.initials("AJ") == "A. J.")
ok("doi prefixes", [C.clean_doi(x) for x in ("doi.org/10.1/x", "https://www.doi.org/10.1/x", "doi: 10.1/x", "https://doi.org/10.1/x")] == ["10.1/x"] * 4)
ps = [paper(["Smith, Z."], 2018, "a"), paper(["Smith, A."], 2020, "b"), paper(["Smith, A."], "n.d.", "c")]
order = [(p["authors"][0], p["year"]) for p in sorted(ps, key=C.sort_key)]
ok("APA sort: initials, n.d. first", order == [("Smith, A.", "n.d."), ("Smith, A.", 2020), ("Smith, Z.", 2018)], order)

# ---- year suffix a/b
lrm = {"title": "T", "papers": [paper(["Smith, J."], 2020, "Zebra study", id="s1"), paper(["Smith, J."], 2020, "A study of apples", id="s2")]}
f = wj("suffix.json", lrm)
rc, out = run("build_lrm.py", f, "--out", f"{T}/suffix.xlsx")
ws = openpyxl.load_workbook(f"{T}/suffix.xlsx")["LRM"]
ok("year suffix a/b", rc == 0 and "(2020a)" in ws["C2"].value and "(2020b)" in ws["C3"].value, (rc, ws["C2"].value, ws["C3"].value))

# ---- first person
import build_lrm as B  # noqa: E402
ok("first person flags", all(B.FIRST_PERSON.search(t) for t in ("We found it", "Our sample", "used by us", "I found that")))
ok("first person spares", not any(B.FIRST_PERSON.search(t) for t in ("Phase I trial", "Type I error", "The US sample")))

# ---- injection + control chars
inj = {"title": "T", "papers": [paper(["Zed, A."], 2021, "Inj", id="inj",
        results='=HYPERLINK("http://evil.example","click")', discussion="PDF\x0cnext page")]}
f = wj("inj.json", inj)
rc, out = run("build_lrm.py", f, "--check")
ok("check passes control chars", rc == 0, out)
rc, out = run("build_lrm.py", f, "--out", f"{T}/inj.xlsx")
ws = openpyxl.load_workbook(f"{T}/inj.xlsx")["LRM"]
ok("build survives control chars", rc == 0, out)
ok("formula text stays text", ws["H2"].data_type == "s" and ws["H2"].value.startswith("="), (ws["H2"].data_type,))

# ---- synthesis/concept keyed by id survive a renumber; stale warning
base = {"title": "T", "papers": [paper(["Tufekci, Z."], 2013, "Not this one", id="tufekci2013"),
                                  paper(["Abdullah, R."], 2021, "Other", id="abdullah2021")]}
syn = {"themes": [{"name": "Attention", "cells": {"tufekci2013": "Tufekci text", "abdullah2021": "Abdullah text"}}]}
con = {"concepts": ["A", "B"], "papers": [{"id": "tufekci2013", "concepts": ["A"]}, {"id": "abdullah2021", "concepts": ["B"]}]}
fl, fs, fc = wj("l.json", base), wj("s.json", syn), wj("c.json", con)
X = f"{T}/m.xlsx"
run("build_lrm.py", fl, "--out", X); run("build_synthesis.py", fs, "--lrm", fl, "--out", X); run("build_concept.py", fc, "--lrm", fl, "--out", X)
base["papers"].insert(0, paper(["Aaron, B."], 1999, "New first", id="aaron1999"))
fl2 = wj("l2.json", base)
rc, out = run("build_lrm.py", fl2, "--out", X)
ok("stale-sheet warning", "WARNING" in out and "Synthesis matrix" in out, out)
run("build_synthesis.py", fs, "--lrm", fl2, "--out", X); run("build_concept.py", fc, "--lrm", fl2, "--out", X)
wb = openpyxl.load_workbook(X)
sy = wb["Synthesis matrix"]
hdr = [c.value for c in sy[1]]
col = {h.split("\n")[1]: i for i, h in enumerate(hdr) if h and "\n" in h and h.startswith("P")}
ok("synthesis text stays on the right paper after renumber",
   sy.cell(2, col["Tufekci (2013)"] + 1).value == "Tufekci text" and sy.cell(2, col["Abdullah (2021)"] + 1).value == "Abdullah text",
   [(h, sy.cell(2, i + 1).value) for h, i in col.items()])
ok("sheet order kept", wb.sheetnames == ["Summary", "LRM", "Synthesis matrix", "Concept matrix"], wb.sheetnames)

# ---- P-code keys warn; unknown key rejected; no-code source; duplicates
rc, out = run("build_synthesis.py", wj("sp.json", {"themes": [{"name": "t", "cells": {"P01": "x"}}]}), "--lrm", fl2, "--check")
ok("P-code key warns", rc == 0 and "position codes" in out, out)
rc, out = run("build_synthesis.py", wj("su.json", {"themes": [{"name": "t", "cells": {"nobody": "x"}}]}), "--lrm", fl2, "--check")
ok("unknown synthesis key rejected", rc == 1 and "not a paper" in out, out)
rc, out = run("build_synthesis.py", wj("sn.json", {"sources": [{"label": "X (2020)"}], "themes": [{"name": "t"}]}), "--check")
ok("source without code: clean error", rc == 1 and "Traceback" not in out and "needs a" in out, out)
rc, out = run("build_concept.py", wj("cu.json", {"concepts": ["A", "B"], "papers": [{"id": "ghost", "concepts": ["B"]}]}), "--lrm", fl2, "--check")
ok("unknown concept paper rejected", rc == 1 and "not in the LRM" in out, out)
rc, out = run("build_concept.py", wj("cd.json", {"concepts": ["A", "a"], "papers": []}), "--lrm", fl2, "--check")
ok("duplicate concepts rejected", rc == 1 and "twice" in out, out)

# ---- formula injection in concept/synthesis names
rc, out = run("build_concept.py", wj("ci.json", {"concepts": ["=1+1", "B"], "papers": [{"id": "tufekci2013", "concepts": ["=1+1"]}]}), "--lrm", fl2, "--out", f"{T}/ci.xlsx")
cs = openpyxl.load_workbook(f"{T}/ci.xlsx")["Concept matrix"]
ok("concept name starting '=' stays text", rc == 0 and cs["B1"].data_type == "s", (rc, out, cs["B1"].data_type))

# ---- crossref: markup, entities, DOI case, retraction, mismatch
cr = {"status": "ok", "message": {"DOI": "10.9999/ABC.1", "title": ["Gene expression in <i>Drosophila</i> larvae"], "subtitle": [],
      "container-title": ["Journal of Physics &amp; Chemistry"], "volume": "3", "issue": "2", "page": "5-9",
      "author": [{"given": "Jean-Pierre", "family": "Dupont"}, {"given": "AJ", "family": "Wakefield"}],
      "published-print": {"date-parts": [[2020, 1]]}, "ISSN": ["1234-5678"]}}
os.makedirs(f"{T}/cr", exist_ok=True)
json.dump(cr, open(f"{T}/cr/10.9999_ABC.1.json", "w"))
mk = {"title": "T", "papers": [paper(["Dupont, J.-P.", "Wakefield, A. J."], 2020, "Gene expression in Drosophila larvae",
      journal="Journal of Physics & Chemistry", volume="3", issue="2", pages="5-9", doi="doi.org/10.9999/abc.1", id="d1")]}
f = wj("mk.json", mk)
rc, out = run("crossref_check.py", f, "--offline", f"{T}/cr")
ok("crossref: markup, entity, DOI case/prefix verified", rc == 0 and "verified" in out, out)
mk["papers"][0]["journal"] = "x"
f = wj("mk2.json", mk)
rc, out = run("crossref_check.py", f, "--offline", f"{T}/cr", "--apply", "--write")
d = json.load(open(f))
ok("--apply writes clean journal, hyphen initials",
   d["papers"][0]["journal"] == "Journal of Physics & Chemistry" and d["papers"][0]["authors"][0] == "Dupont, J.-P.", d["papers"][0])
os.makedirs(f"{T}/crx", exist_ok=True)
for fn in os.listdir(EX + "/crossref"):
    open(f"{T}/crx/{fn}", "w").write(open(f"{EX}/crossref/{fn}").read())
rt = json.load(open(EX + "/lrm.retracted-test.json"))
rt["papers"][1]["authors"] = ["Tufecki, Z."]
f = wj("rt.json", rt)
rc, out = run("crossref_check.py", f, "--offline", f"{T}/crx", "--write")
d = json.load(open(f))
ok("retraction found", any(n["type"] == "retraction" for n in d["papers"][0].get("notices", [])), d["papers"][0].get("notices"))
ok("misspelt surname caught", rc == 1 and "Tufecki" in out, out)

# ---- scimago
pg = EX + "/scimago_24733.md"
rc, out = run("scimago_quartile.py", "--journal-page", pg, "--year", "2013", "--category", "Education")
ok("scimago education 2013 Q2", out.startswith("Q2 (SJR 2013, Education)"), out)
rc, out = run("scimago_quartile.py", "--journal-page", pg, "--year", "2030")
ok("scimago future year clamps with note", "used 2025" in out and out.startswith("Q1"), out)
rc, out = run("scimago_quartile.py", "--journal-page", pg, "--year", "2013", "--category", "Physics")
ok("scimago unknown category", out.startswith("Unranked/Unavailable"), out)
tbl = {"Arts": {2018: "Q1", 2019: "Q1"}, "Education": {2018: "Q2", 2019: "Q2", 2020: "Q2"}}
import scimago_quartile as S  # noqa: E402
cell, note = S.cell_text(tbl, 2020, "Arts")
ok("scimago: category left the year -> Unavailable, not a wrong year", cell == "Unranked/Unavailable" and note and "2019" not in cell, (cell, note))

# ---- end to end + recalc
full = EX + "/lrm.example.json"
Xf = f"{T}/full.xlsx"
run("build_lrm.py", full, "--out", Xf)
run("build_synthesis.py", wj("s2.json", {"themes": [{"name": "t", "cells": {"10.1177/0002764213479369": "x"}}]}), "--lrm", full, "--out", Xf)
run("build_concept.py", wj("c2.json", {"concepts": ["A"], "papers": [{"doi": "10.1177/0002764213479369", "concepts": ["A"]}]}), "--lrm", full, "--out", Xf)
if RECALC:
    p = subprocess.run([sys.executable, RECALC, Xf, "90"], capture_output=True, text=True)
    res = json.loads(p.stdout[p.stdout.index("{"):])
    ok("recalc: zero formula errors", res.get("status") == "success" and res.get("total_errors") == 0, res)
else:
    print("SKIP recalc: no xlsx skill recalc.py found (set RECALC=path)")
ok("no PDF/reportlab left", subprocess.run(["grep", "-rli", "reportlab", SC], capture_output=True).returncode == 1)

bad = [n for n, c in RESULTS if not c]
print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed" + (f"; FAILED: {bad}" if bad else ""))
sys.exit(1 if bad else 0)
