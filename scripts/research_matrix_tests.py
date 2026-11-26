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
         "type": "Quantitative", "quartile": "Unranked/Unavailable"}
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

# ---- evidence check: the "paper says AB, cell says ABC" cases
pdir = f"{T}/papers"
os.makedirs(pdir, exist_ok=True)
open(f"{pdir}/app2022.txt", "w").write(
    "Methods\nWe surveyed 120 teachers in one dis-\ntrict using a short questionnaire.\n"
    "Results\nUse of the app may be associated with higher scores (r = .21, p = .04).\n")
good = paper(["Lim, K."], 2022, "App use and scores", id="app2022", source_basis="full text",
             methodology="A survey of 120 teachers in one district, using a short questionnaire.",
             results="App use may be associated with higher scores (r = .21, p = .04).",
             evidence={"methodology": [{"q": "We surveyed 120 teachers in one district using a short questionnaire", "loc": "Methods"}],
                       "results": [{"q": "Use of the app may be associated with higher scores (r = .21, p = .04)", "loc": "Results"}]})
rc, out = run("check_evidence.py", wj("ev_good.json", {"papers": [good]}), "--papers", pdir)
ok("evidence: faithful cells pass (hyphenated line break matched)", rc == 0 and "WARN" not in out, out)
abc = json.loads(json.dumps(good))
abc["results"] = "Using the app leads to higher scores among 300 Malaysian secondary teachers (r = .21)."
rc, out = run("check_evidence.py", wj("ev_abc.json", {"papers": [abc]}), "--papers", pdir)
ok("evidence: added number caught", rc == 1 and "300" in out, out)
ok("evidence: dropped hedge warned", "hedged" in out, out)
ok("evidence: causal wording warned", "leads to" in out, out)
fake = json.loads(json.dumps(good))
fake["evidence"]["results"] = [{"q": "App use caused a large improvement in scores", "loc": "Results"}]
rc, out = run("check_evidence.py", wj("ev_fake.json", {"papers": [fake]}), "--papers", pdir)
ok("evidence: invented quote caught", rc == 1 and "quote not found" in out, out)
noev = json.loads(json.dumps(good))
noev["evidence"] = {"methodology": noev["evidence"]["methodology"]}
rc, out = run("check_evidence.py", wj("ev_noev.json", {"papers": [noev]}), "--papers", pdir)
ok("evidence: filled cell without quotes caught", rc == 1 and "no quotes" in out, out)
nofile = json.loads(json.dumps(good)); nofile["id"] = "ghost2022"
rc, out = run("check_evidence.py", wj("ev_nofile.json", {"papers": [nofile]}), "--papers", pdir)
ok("evidence: missing saved text caught", rc == 1 and "no saved text" in out, out)
rc, out = run("build_lrm.py", wj("ev_build.json", {"title": "T", "papers": [good]}), "--out", f"{T}/ev.xlsx")
smx = openpyxl.load_workbook(f"{T}/ev.xlsx")["Summary"]
ok("Summary shows what each row was read from", rc == 0 and smx["E11"].value == "Read from" and smx["E12"].value == "full text",
   (rc, smx["E11"].value, smx["E12"].value))

# ---- abstract overclaims: only that finding is coloured, both quotes checked
open(f"{pdir}/read2023.txt", "w").write(
    "Abstract\nThe programme dramatically improved reading for all pupils.\n"
    "Results\nFluency rose by 12 words per minute. Comprehension scores did not change. "
    "Gains were observed only among Year 4 pupils (n = 38).\n")
f3 = "Gains were seen only among Year 4 pupils (n = 38)."
oc_p = paper(["Ng, S."], 2023, "Reading programme", id="read2023", source_basis="full text",
             results=f"Fluency rose by 12 words per minute. Comprehension did not change. {f3}",
             evidence={"results": [{"q": "Fluency rose by 12 words per minute", "loc": "Results"},
                                   {"q": "Comprehension scores did not change", "loc": "Results"}]},
             overclaims=[{"field": "results", "text": f3,
                          "abstract": "The programme dramatically improved reading for all pupils",
                          "body": "Gains were observed only among Year 4 pupils (n = 38)", "body_loc": "Results"}])
fo = wj("oc.json", {"title": "T", "papers": [oc_p]})
rc, out = run("check_evidence.py", fo, "--papers", pdir)
ok("overclaim: body and abstract quotes verified", rc == 0, out)
rc, out = run("build_lrm.py", fo, "--out", f"{T}/oc.xlsx")
wsx = openpyxl.load_workbook(f"{T}/oc.xlsx", rich_text=True)["LRM"]
cellx = wsx["H2"]
runs = [(str(b.text) if hasattr(b, "text") else str(b), getattr(getattr(b, "font", None), "color", None)) for b in cellx.value]
coloured = [t for t, c in runs if c is not None and "BF9000" in str(c.rgb if hasattr(c, "rgb") else c)]
plain = [t for t, c in runs if t not in coloured]
ok("overclaim: only finding 3 is yellow", coloured == [f3] and any("Fluency" in t for t in plain), runs)
ok("overclaim: hover note quotes abstract and body", cellx.comment is not None and "dramatically" in cellx.comment.text
   and "Year 4" in cellx.comment.text, cellx.comment.text if cellx.comment else None)
bad = json.loads(json.dumps(oc_p)); bad["overclaims"][0]["text"] = "words not in the cell"
rc, out = run("build_lrm.py", wj("oc_bad.json", {"title": "T", "papers": [bad]}), "--check")
ok("overclaim: text must be in the cell", rc == 1 and "exact words" in out, out)
leak = json.loads(json.dumps(oc_p))
leak["overclaims"][0]["abstract"] = "The programme raised reading scores by 40 points for all pupils"
leak["results"] = leak["results"].replace("(n = 38).", "(n = 38), by 40 points.")
leak["overclaims"][0]["text"] = leak["results"].split(" Comprehension did not change. ")[1]
open(f"{pdir}/read2023.txt", "a").write("Abstract2\nThe programme raised reading scores by 40 points for all pupils.\n")
rc, out = run("check_evidence.py", wj("oc_leak.json", {"papers": [leak]}), "--papers", pdir)
ok("overclaim: abstract's number cannot leak into the cell", rc == 1 and "come from the abstract" in out, out)

# ---- merge helper output
ho = f"{T}/helper_out"
os.makedirs(ho, exist_ok=True)
json.dump(paper(["Aaa, A."], 2020, "First", id="aaa2020", results="Read result.", quartile="Q4 (SJR 1999, Wrong)"), open(f"{ho}/aaa2020.json", "w"))
json.dump([paper(["Bbb, B."], 2021, "Second", id="bbb2021")], open(f"{ho}/bbb2021.json", "w"))
open(f"{ho}/broken.json", "w").write("{not json")
json.dump({"title": "T", "papers": [paper(["Aaa, A."], 2020, "OLD TITLE", id="aaa2020", quartile="Q1 (SJR 2020, Education)", crossref="verified")]}, open(f"{T}/m.json", "w"))
rc, out = run("merge_papers.py", f"{T}/m.json", "--from", ho)
dm = json.load(open(f"{T}/m.json"))
pa = next(p for p in dm["papers"] if p["id"] == "aaa2020")
ok("merge: adds, updates by id, skips broken file, keeps top-level fields",
   rc == 1 and "1 added, 1 replaced, 1 skipped" in out and len(dm["papers"]) == 2 and dm["title"] == "T" and pa["results"] == "Read result.", out)
ok("merge: an existing paper keeps its checked title, quartile and Crossref status (the reading file cannot overwrite them)",
   pa["title"] == "OLD TITLE" and pa["quartile"] == "Q1 (SJR 2020, Education)" and pa["crossref"] == "verified", pa)
rc, out = run("merge_papers.py", f"{T}/new.json", "--from", ho)
ok("merge: creates lrm.json when missing", os.path.exists(f"{T}/new.json"), out)

# ---- evidence check: text from a web page keeps markdown marks the reader does not type
open(f"{pdir}/web2024.txt", "w").write("The sample ( _n_ = 103) had a mean of 3.2 \\[SD 0.4\\], and **p** < .001.\n")
web = paper(["Wu, X."], 2024, "Web text", id="web2024", source_basis="full text",
            results="The sample (n = 103) had a mean of 3.2.",
            evidence={"results": [{"q": "The sample (n = 103) had a mean of 3.2 [SD 0.4], and p < .001", "loc": "Results"}]})
rc, out = run("check_evidence.py", wj("ev_web.json", {"papers": [web]}), "--papers", pdir)
ok("evidence: markdown emphasis and escapes in the page text do not fail an honest quote", rc == 0, out)

# ---- apply_overclaims: pairing reply -> coloured sentence, notes, dropped fakes
open(f"{pdir}/pair2025.txt", "w").write(
    "Abstract\nThe programme dramatically improved reading for all pupils.\n"
    "Results\nFluency rose by 12 words per minute. Comprehension scores did not change. "
    "Gains were observed only among Year 4 pupils (n = 38).\n")
pp = paper(["Roy, T."], 2025, "Pairing test", id="pair2025", source_basis="full text",
           results="Fluency rose by 12 words per minute. Comprehension did not change. Gains were seen only among Year 4 pupils (n = 38).",
           evidence={"results": [{"q": "Fluency rose by 12 words per minute", "loc": "Results"}]},
           abstract_claims=[{"q": "The programme dramatically improved reading for all pupils", "loc": "Abstract"}],
           caveats=[{"q": "Gains were observed only among Year 4 pupils (n = 38)", "loc": "Results"}])
fp = wj("pair_lrm.json", {"title": "T", "papers": [pp]})
rc, out = run("check_evidence.py", fp, "--papers", pdir)
ok("evidence: the reader's abstract_claims and caveats are checked against the text", "ERROR" not in out and rc in (0,), out)
badcav = json.loads(json.dumps(pp)); badcav["caveats"].append({"q": "Effects vanished after six months", "loc": "Discussion"})
rc, out = run("check_evidence.py", wj("pair_badcav.json", {"papers": [badcav]}), "--papers", pdir)
ok("evidence: an invented caveat quote is caught", rc == 1 and "quote not found" in out, out)
po = f"{T}/pairing_out"; os.makedirs(po, exist_ok=True)
good = {"abstract": "The programme dramatically improved reading for all pupils", "body": "Gains were observed only among Year 4 pupils (n = 38)",
        "body_loc": "Results", "cell_sentence_id": "results.3", "why": "only Year 4"}
fake = {"abstract": "The programme dramatically improved reading for all pupils", "body": "Gains vanished after six months",
        "cell_sentence_id": "results.2"}
loose = {"abstract": "The programme dramatically improved reading for all pupils", "body": "Comprehension scores did not change",
         "cell_sentence_id": None, "body_loc": "Results"}
open(f"{po}/pair2025.json", "w").write("Here is my answer:\n" + json.dumps({"overclaims": [fake], "unsettled": []}) +
    "\n\nCorrection: that entry is invalid. Corrected output:\n" +
    json.dumps({"overclaims": [good, fake, loose], "unsettled": ["The programme dramatically improved reading for all pupils"]}))
rc, out = run("apply_overclaims.py", fp, "--from", po, "--papers", pdir)
dp = json.load(open(fp))["papers"][0]
ok("apply: last JSON object used; 1 coloured, 1 noted, fake dropped, 1 unsettled",
   rc == 0 and "1 coloured, 1 noted, 1 dropped, 1 unsettled" in out and len(dp["overclaims"]) == 1
   and dp["overclaims"][0]["text"] == "Gains were seen only among Year 4 pupils (n = 38).", out)
rc, out = run("build_lrm.py", fp, "--out", f"{T}/pair.xlsx")
wbp = openpyxl.load_workbook(f"{T}/pair.xlsx", rich_text=True)
cl = wbp["LRM"]["H2"]
ok("apply: the placed sentence is coloured with a hover note", cl.comment is not None and "Year 4" in cl.comment.text
   and any(getattr(getattr(b, "font", None), "color", None) is not None for b in cl.value if not isinstance(b, str)), None)
sm_ = wbp["Summary"]
ok("apply: noted and unsettled items appear on the Summary sheet", sm_["F11"].value is not None and "Comprehension scores did not change" in (sm_["F12"].value or "")
   and "To check" in (sm_["F12"].value or ""), sm_["F12"].value)

# ---- no Access column
rc, out = run("build_lrm.py", EX + "/lrm.example.json", "--out", f"{T}/noaccess.xlsx")
wsn = openpyxl.load_workbook(f"{T}/noaccess.xlsx")["LRM"]
hdr = [c.value for c in wsn[1]]
ok("LRM has 11 columns: Limitations and future research before Quartile, no Access; filter covers A:K",
   rc == 0 and hdr[-1] == "Quartile" and hdr[-2] == "Limitations and future research" and "Access" not in hdr
   and len(hdr) == 11 and wsn.auto_filter.ref.startswith("A1:K"), hdr)
lim_col = [wsn.cell(row=r, column=10).value for r in range(2, wsn.max_row + 1)]
ok("an unfilled limitations cell prints Not explicitly stated", "Not explicitly stated" in lim_col and any(v and v.startswith("Placeholder") for v in lim_col), lim_col)
rc, out = run("build_lrm.py", wj("oldaccess.json", {"papers": [dict(paper(["Tan, A."], 2020, "T"), access="Free", doi="10.1/x")]}), "--check")
ok("a leftover access field in old JSON is ignored, not an error", rc == 0 and "access" not in out.lower(), out)


# ---- limitations column and the gap list
lim_dir = f"{T}/limpapers"; os.makedirs(lim_dir, exist_ok=True)
open(f"{lim_dir}/lim1.txt", "w").write("Results were clear. A limitation is that only one school took part. Future studies should follow pupils for two years.")
lp1 = paper(["Adams, A. B."], 2020, "First paper", id="lim1", doi="10.1/lim1", methodology="Pupils at one school were taught.",
            limitations="Only one school took part, and the authors call for following pupils for two years.",
            evidence={"methodology": [{"q": "only one school took part", "loc": "Limits"}],
                      "limitations": [{"q": "only one school took part", "loc": "Limits"},
                                      {"q": "Future studies should follow pupils for two years", "loc": "Limits"}]})
lp2 = paper(["Brown, C. D."], 2021, "Second paper", id="lim2", doi="10.1/lim2", limitations="Self-report measures were used.")
lj = wj("lim.json", {"title": "T", "papers": [lp1, lp2]})
rc, out = run("check_evidence.py", lj, "--papers", lim_dir)
ok("evidence: the limitations cell is checked like the others (lim2 has none: error)", rc == 1 and "limitations: filled cell has no quotes" in out and "lim1" not in out.split("ERROR")[1] if "ERROR" in out else False, out)
bad_l = json.loads(json.dumps(lp1)); bad_l["limitations"] = "Only one school took part. The sample had 250 pupils."
rc, out = run("check_evidence.py", wj("lim_bad.json", {"papers": [bad_l]}), "--papers", lim_dir)
ok("evidence: a number in the limitations cell that no quote has is an error", rc == 1 and "250" in out, out)
gp = {"title": "T", "papers": [lp1, lp2],
      "gaps": [{"gap": "Among these 2 papers, the authors of lim1 call for following pupils for two years.", "kind": "stated by authors",
                "papers": ["lim1"], "basis": "limitations cell of lim1"},
               {"gap": "Among these 2 papers, only self-report measures appear in lim2.", "kind": "across papers", "papers": ["10.1/lim2", "lim1"]}]}
rc, out = run("build_lrm.py", wj("gap_ok.json", gp), "--out", f"{T}/gap_ok.xlsx")
wg = openpyxl.load_workbook(f"{T}/gap_ok.xlsx")["Summary"]
cells = {c.value: c for row in wg.iter_rows() for c in row if isinstance(c.value, str)}
rows_g = [r for r in wg.iter_rows(values_only=True) if r[0] in ("Stated by authors", "Across papers")]
ok("gap list: appears on the Summary sheet with P-codes and a live count formula",
   rc == 0 and len(rows_g) == 2 and rows_g[0][3] == "P01" and rows_g[1][3] == "P01, P02" and "Research gaps" in cells
   and str(rows_g[1][4]).startswith("=IF("), rows_g)
for name, mut, needle in [
    ("a P-code is refused", {"papers": ["P01"]}, "P-code"),
    ("an unknown paper is refused", {"papers": ["nobody1999"]}, "not the id or DOI"),
    ("a gap with no papers is refused", {"papers": []}, "must name the papers"),
    ("a bad kind is refused", {"kind": "my opinion"}, "kind must be"),
]:
    g2 = json.loads(json.dumps(gp)); g2["gaps"][0].update(mut)
    rc, out = run("build_lrm.py", wj("gap_bad.json", g2), "--check")
    ok("gap list: " + name, rc != 0 and needle in out, out)
g3 = json.loads(json.dumps(gp)); g3["gaps"][0]["gap"] = "Nobody has studied pupils beyond one year."
rc, out = run("build_lrm.py", wj("gap_abs.json", g3), "--check")
ok("gap list: a claim about the whole field draws a warning", rc == 0 and "whole field" in out, out)
g4 = json.loads(json.dumps(gp)); g4["gaps"][0]["gap"] = "Among these 2 papers, the authors of lim1 call for longer follow-up because the effect may fade."
rc, out = run("build_lrm.py", wj("gap_why.json", g4), "--check")
ok("gap list: a gap that explains with 'because' draws a warning", rc == 0 and '"because"' in out, out)
gpath = wj("gaps_w.json", {"gaps": [
    {"gap": "Among these 2 papers, the authors of lim1 call for following pupils for two years.", "kind": "stated by authors", "papers": ["lim1"], "basis": "b"},
    {"gap": "Among these 2 papers, every sample is one school.", "kind": "across papers", "papers": ["lim1", "lim2"], "basis": "b"},
    {"gap": "Nobody has ever tested this.", "kind": "across papers", "papers": ["lim2"], "basis": "b"},
    {"gap": "Among these 2 papers, lim2 is a thesis.", "kind": "across papers", "papers": ["ghost"], "basis": "b"},
    {"gap": "Among these 2 papers, unchecked one.", "kind": "across papers", "papers": ["lim1"], "basis": "b"}]})
vpath = f"{T}/gaps_v.json"
open(vpath, "w").write("thinking...\n" + json.dumps({"verdicts": [{"id": "gap.1", "verdict": "cut"}]}) + "\nCorrected: " + json.dumps({"verdicts": [
    {"id": "gap.1", "verdict": "keep", "reason": "ok"},
    {"id": "gap.2", "verdict": "narrow", "narrowed": "Among these 2 papers, lim1 is from one school.", "reason": "lim2 says nothing"},
    {"id": "gap.3", "verdict": "cut", "reason": "field claim"},
    {"id": "gap.4", "verdict": "keep"}]}))
lg = wj("lim_apply.json", {"title": "T", "papers": [lp1, lp2]})
rc, out = run("apply_gaps.py", lg, "--gaps", gpath)
ok("apply_gaps: refuses to write without verdicts", rc == 1 and "no --verdicts" in out and "gaps" not in json.load(open(lg)), out)
rc, out = run("apply_gaps.py", lg, "--gaps", gpath, "--verdicts", vpath)
gw = json.load(open(lg)).get("gaps", [])
ok("apply_gaps: last verdict object used; keep, narrow (new text), cut, unknown paper and unchecked dropped",
   rc == 0 and len(gw) == 2 and gw[1]["gap"] == "Among these 2 papers, lim1 is from one school." and "kept 1, narrowed 1, cut 1, unchecked 1, no paper left 1" in out, out)
rc, out = run("build_lrm.py", lg, "--check")
ok("apply_gaps: the written gaps pass the build check", rc == 0, out)


# ---- helper inputs and verdicts
hp = paper(["Adams, A. B."], 2020, "First", id="h1", doi="10.1/h1", methodology="Pupils at one school were taught. They were tested twice. The sample was random.",
           results="Fluency rose. Comprehension did not change.", limitations="Only one school took part.",
           evidence={"methodology": [{"q": "Pupils at one school were taught", "loc": "M"}], "results": [{"q": "Fluency rose", "loc": "R"}],
                     "limitations": ["only one school took part"]},
           abstract_claims=[{"q": "The programme improved reading for all pupils", "loc": "Abstract"}], caveats=[{"q": "Comprehension did not change", "loc": "R"}],
           overclaims=[{"field": "results", "text": "Fluency rose.", "abstract": "The programme improved reading for all pupils", "body": "Comprehension did not change"}])
hl = wj("help.json", {"title": "T", "papers": [hp]})
pin = f"{T}/pairing_in"; vin_ = f"{T}/verify_in"; gin = f"{T}/gaps_in"
rc1, o1 = run("prepare_helper_inputs.py", hl, "--kind", "pairing", "--out", pin)
rc2, o2 = run("prepare_helper_inputs.py", hl, "--kind", "verify", "--out", vin_)
rc3, o3 = run("prepare_helper_inputs.py", hl, "--kind", "gaps", "--out", gin, "--title", "My title")
pj, vj, gj = (json.load(open(f"{pin}/h1.json")), json.load(open(f"{vin_}/h1.json")), json.load(open(f"{gin}/gap_input.json")))
ok("helper inputs: pairing has abstract claims, body quotes and cell sentences with ids",
   rc1 == 0 and pj["abstract_claims"] == ["The programme improved reading for all pupils"] and pj["body_quotes"]["caveats"] == ["Comprehension did not change"]
   and {"id": "results.2", "sentence": "Comprehension did not change."} in pj["cell_sentences"], pj)
ok("helper inputs: verify has every column's sentences, quotes and the overclaim",
   rc2 == 0 and any(s["id"] == "limitations.1" for s in vj["sentences"]) and vj["quotes"]["limitations"] == ["only one school took part"]
   and vj["overclaims"][0]["id"] == "overclaim.1", vj)
ok("helper inputs: gaps file carries title and the two cells per paper", rc3 == 0 and gj["title"] == "My title" and gj["papers"][0]["limitations"] == "Only one school took part.", gj)
vo = f"{T}/verify_out"; os.makedirs(vo, exist_ok=True)
open(f"{vo}/h1.json", "w").write("note\n" + json.dumps({"verdicts": [
    {"id": "methodology.1", "verdict": "keep"}, {"id": "methodology.2", "verdict": "narrow", "reason": "twice not quoted", "support": "twice"},
    {"id": "methodology.3", "verdict": "cut", "reason": "random is not quoted"}, {"id": "results.1", "verdict": "keep"},
    {"id": "results.2", "verdict": "keep"}, {"id": "overclaim.1", "verdict": "cut"}]}))
hl2 = wj("help2.json", json.load(open(hl)))
rc, out = run("apply_verdicts.py", hl2, "--from", vo)
d2 = json.load(open(hl2))["papers"][0]
ok("verdicts: cut removes the sentence, narrow is only listed, an unverified sentence is listed, a cut overclaim is removed",
   rc == 0 and d2["methodology"] == "Pupils at one school were taught. They were tested twice." and "NARROW" in out and "limitations.1: no verdict" in out
   and d2["overclaims"] == [], (out, d2["methodology"]))
hl3 = wj("help3.json", json.load(open(hl)))
rc, out = run("apply_verdicts.py", hl3, "--from", vo, "--narrow", "drop")
ok("verdicts: --narrow drop removes the narrowed sentence too, and adds no words",
   json.load(open(hl3))["papers"][0]["methodology"] == "Pupils at one school were taught.", out)

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
