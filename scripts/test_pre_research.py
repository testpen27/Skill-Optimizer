#!/usr/bin/env python3
"""Regression tests for the pre-research skill's scripts.

    python3 scripts/test_pre_research.py

No network needed: OpenAlex is replaced by a recorded response and the
download sites by a local web server. Malformed input must fail with a
one-line error (exit 1, no stack trace).
"""
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "skills/pre-research/scripts/search_tool.js"
EXAMPLE = TOOL.parent.parent / "examples/example_spec.json"
failures = []


def run(*args):
    p = subprocess.run(["node", str(TOOL), *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        failures.append(f"{name}: {detail}")


def spec(tmp, obj, raw=None):
    f = Path(tmp) / "s.json"
    f.write_text(raw if raw is not None else json.dumps(obj))
    return str(f)


with tempfile.TemporaryDirectory() as tmp:
    for name, obj, raw, want in [
        ("invalid JSON", None, "{bad", "not valid JSON"),
        ("no concepts", {"title": "x"}, None, '"concepts" must be'),
        ("terms is a string", {"concepts": [{"name": "a", "terms": "oops"}]}, None, "non-empty array"),
        ("empty terms", {"concepts": [{"name": "a", "terms": []}]}, None, "non-empty array"),
        ("non-string term", {"concepts": [{"name": "a", "terms": [1]}]}, None, "must be a string"),
        ("bad years", {"years": ["a", "b"], "concepts": [{"name": "a", "terms": ["x"]}]}, None, "whole years"),
    ]:
        rc, out, err = run("strings", spec(tmp, obj, raw))
        check(name, rc == 1 and want in err and "\n    at " not in err, f"rc={rc} err={err[:120]}")

    rc, out, err = run("strings", str(Path(tmp) / "missing.json"))
    check("missing file", rc == 1 and "Cannot read" in err)

    rc, out, _ = run("strings", spec(tmp, {"years": [2026, 2022], "concepts": [{"name": "a", "terms": ["alpha*", "beta*", "gamma*"]}]}))
    check("reversed years are swapped", "PUBYEAR > 2021 AND PUBYEAR < 2027" in out and "swapped" in out)

    rc, out, _ = run("strings", spec(tmp, {"concepts": [{"name": "a", "terms": ["“video on demand”", "netflix*", "viu*"]}]}))
    check("curly quotes are converted", '"video on demand"' in out and "“" not in out.split("## Warnings")[0])

    rc, out, _ = run("strings", spec(tmp, {"concepts": [{"name": "a", "terms": ["\"news organi?ation*\"", "ai*", "Netflix AND Viu", "behavio$r"]}]}))
    for name, want in [("short stem", "Keep at least 3"), ("operator in term", "operator word"), ("dollar sign", "uses $")]:
        check(f"warns: {name}", want in out)
    check("no warning for wildcard inside a quoted phrase", "inside the quoted phrase" not in out)

    rc, out, _ = run("strings", str(EXAMPLE))
    check("example spec has no hard warnings", "unbalanced" not in out and "Fixed:" not in out)

    rc, out, err = run("docx", str(EXAMPLE), str(Path(tmp) / "o.docx"))
    check("docx mode is gone with a clear error", rc == 1 and "Unknown mode" in err)

    rc, out, _ = run("strings", spec(tmp, {"ranges": [[2016, 2020], [2026, 2021]], "concepts": [
        {"name": "a", "terms": ["alpha*", "beta*", "gamma*"]}, {"name": "b", "terms": ["delta*", "eps*", "zeta*"]},
        {"name": "c", "terms": ["eta*", "theta*", "iota*"]}]}))
    check("two ranges, second swapped", "PUBYEAR > 2015 AND PUBYEAR < 2021" in out and "PUBYEAR > 2020 AND PUBYEAR < 2027" in out and "swapped" in out)
    check("default tiers for three concepts", "broad = concepts 1, 2; balanced = concepts 1, 2, 3" in out)
    rc, out, err = run("strings", spec(tmp, {"tiers": {"x": [1, 5]}, "concepts": [{"name": "a", "terms": ["alpha*"]}]}))
    check("tier with a missing concept is rejected", rc == 1 and "concept numbers from 1 to 1" in err)
    rc, out, _ = run("plan", str(EXAMPLE))
    plan = json.loads(out)
    check("plan has a row per tier x range x database", len(plan["runs"]) == 18 and all(r["hits"] is None for r in plan["runs"]))
    check("plan Scholar rows carry the year limits", any("as_ylo=2016&as_yhi=2020" in (r["url"] or "") for r in plan["runs"]))

    for name, s, kind, want in [
        ("check: curly quotes", "(“OTT” OR Netflix)", "scholar", "curly quotes"),
        ("check: unbalanced brackets", "TITLE-ABS-KEY((a OR b)", "scopus", "unbalanced parentheses"),
        ("check: scholar wildcard", "adopt* AND tv", "scholar", "does not support"),
        ("check: wrong database codes", "TS=(a OR b)", "scopus", "Web of Science field codes"),
        ("check: scholar too long", "a " * 200, "scholar", "256"),
    ]:
        rc, out, _ = run("check", s, kind)
        check(name, want in out, out[-120:])


# ---------------------------------------------------------------- Python scripts
import contextlib
import functools
import http.server
import importlib.util
import io
import threading

SCRIPTS = TOOL.parent


def module(name):
    spec_ = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    m = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(m)
    return m


oa = module("openalex")
rt = module("retrieve")

# OpenAlex query conversion
q, wild, notes = oa.openalex_query([
    {"terms": ['"video on demand"', "adopt*", "*ology", "ai*", "behavio$r"]}, {"terms": ["Malaysia*"]}], [1, 2])
check("openalex: drops leading and short wildcards with a note", "*ology" not in q and "ai*" not in q and len(notes) == 2)
check("openalex: $ becomes *", "behavio*r" in q and wild)
check("openalex: wildcard query uses the exact search", "search.title_abstract_keywords.exact" in oa.search_params(q, wild, 2021, 2026))
check("openalex: no wildcard uses the stemmed search", "search.title_abstract_keywords" in oa.search_params('"a b"', False, 2021, 2026))

# A recorded OpenAlex work (trimmed from a real response, October 2026)
WORK = {"id": "https://openalex.org/W4390583047", "doi": "https://doi.org/10.6007/ijarbss/v13-i12/20380",
        "title": "Exploring The Meaning of Using Vod (Video on Demand) Didik TV", "publication_year": 2023,
        "authorships": [{"author": {"display_name": "Zaiemilia Mohd Rokhani"}}],
        "open_access": {"is_oa": True, "oa_status": "diamond", "oa_url": "https://hrmars.com/x.pdf"},
        "best_oa_location": {"pdf_url": "https://hrmars.com/x.pdf", "license": "cc-by", "landing_page_url": "http://dx.doi.org/10.6007/ijarbss/v13-i12/20380"},
        "primary_location": {"landing_page_url": "http://dx.doi.org/10.6007/ijarbss/v13-i12/20380",
                             "source": {"display_name": "IJARBSS", "host_organization_name": "HRMARS"}}}
rec = oa.from_openalex(WORK)
check("openalex: record fields", rec["doi"] == "10.6007/ijarbss/v13-i12/20380" and rec["pdf_url"] and rec["is_oa"] and rec["publisher"] == "HRMARS")

with tempfile.TemporaryDirectory() as tmp:
    log_path = Path(tmp) / "log.json"
    log_path.write_text(run("plan", str(EXAMPLE))[1])
    calls = []
    oa.http_get = lambda url, timeout=60: calls.append(url) or {"meta": {"count": 528}, "results": []}
    with contextlib.redirect_stdout(io.StringIO()):
        oa.main(["count", str(log_path)])
    rows = [r for r in json.loads(log_path.read_text())["runs"] if r["database"] == "OpenAlex"]
    check("openalex count: one row per tier x range, labelled approximate",
          len(rows) == 6 and all(r["hits"] == 528 and "approximation" in r["note"] for r in rows))
    check("openalex count: year filter sent", any("publication_year%3A2016-2020" in c or "publication_year:2016-2020" in c for c in calls))

    # Export import and de-duplication
    (Path(tmp) / "scopus.csv").write_text(
        'Authors,Author full names,Title,Year,Source title,DOI,Link,Publisher\n'
        '"A","Rokhani, Z","Exploring the meaning of VOD",2023,"IJARBSS","10.6007/IJARBSS/v13-i12/20380","x","HRMARS"\n'
        '"B","Lee, A","Netflix continuance",2022,"J","10.1000/t.2","x","Elsevier"\n', encoding="utf-8-sig")
    (Path(tmp) / "wos.txt").write_text(
        "FN Clarivate Analytics Web of Science\nVR 1.0\nPT J\nAU Rokhani, Z\nTI Exploring the meaning of VOD\nPY 2023\n"
        "DI 10.6007/ijarbss/v13-i12/20380\nER\n\nPT J\nAU Wong, D\nTI Streaming platforms and\n   Malaysian audiences\nPY 2025\nER\nEF\n")
    out_path = Path(tmp) / "records.json"
    with contextlib.redirect_stdout(io.StringIO()):
        rc = oa.main(["import", str(Path(tmp) / "scopus.csv"), str(Path(tmp) / "wos.txt"), "--out", str(out_path)])
    data = json.loads(out_path.read_text())
    check("import: merges Scopus and WoS, removes the duplicate DOI",
          rc == 0 and len(data["records"]) == 3 and data["duplicates_removed"] == 1
          and data["identification"] == {"Scopus": 2, "Web of Science": 2})
    check("import: WoS continuation lines joined", any(r["title"] == "Streaming platforms and Malaysian audiences" for r in data["records"]))
    (Path(tmp) / "bad.csv").write_text("hello,world\n1,2\n")
    with contextlib.redirect_stderr(io.StringIO()) as err:
        rc = oa.main(["import", str(Path(tmp) / "bad.csv"), "--out", str(out_path)])
    check("import: unknown file gives a one-line error", rc == 1 and "not a Scopus CSV" in err.getvalue())

    # Downloads against a local web server
    site = Path(tmp) / "site"
    (site / "oa").mkdir(parents=True)
    (site / "blocked").mkdir()
    pdf = b"%PDF-1.4\n" + b"0" * 3000 + b"\n%%EOF\n"
    (site / "oa" / "good.pdf").write_bytes(pdf)
    (site / "blocked" / "b.pdf").write_bytes(pdf)
    (site / "oa" / "landing.pdf").write_bytes(b"<html><body>verify you are human</body></html>" * 100)
    (site / "oa" / "cut.pdf").write_bytes(pdf[:2000])
    (site / "robots.txt").write_text("User-agent: *\nDisallow: /blocked/\n")
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    handler = functools.partial(Quiet, directory=str(site))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    recs = {"records": [
        {"doi": "10.1/good", "title": "Good open paper", "year": 2024, "authors": ["Tan, Ben"], "is_oa": True, "pdf_url": base + "/oa/good.pdf"},
        {"doi": "10.1/blocked", "title": "Blocked by robots", "year": 2024, "authors": [], "is_oa": True, "pdf_url": base + "/blocked/b.pdf"},
        {"doi": "10.1/landing", "title": "Landing page", "year": 2024, "authors": [], "is_oa": True, "pdf_url": base + "/oa/landing.pdf"},
        {"doi": "10.1/cut", "title": "Truncated", "year": 2024, "authors": [], "is_oa": True, "pdf_url": base + "/oa/cut.pdf"},
        {"doi": "10.1/pay", "title": "Paywalled paper", "year": 2022, "authors": ["Lee, Alice"], "is_oa": False},
        {"doi": "10.1/many", "title": "Over the cap", "year": 2022, "authors": [], "is_oa": True, "pdf_url": base + "/oa/good.pdf"},
    ]}
    rpath = Path(tmp) / "r.json"
    rpath.write_text(json.dumps(recs))
    dest = Path(tmp) / "papers"
    with contextlib.redirect_stdout(io.StringIO()):
        rt.main(["download", str(rpath), "--dest", str(dest), "--max", "4"])
    items = {i["doi"]: i for i in json.loads((dest / "manifest.json").read_text())["items"]}
    check("download: open-access PDF saved with a readable name",
          items["10.1/good"]["status"] == "downloaded" and (dest / "Tan_2024_Good_open_paper.pdf").exists())
    check("download: robots.txt respected", items["10.1/blocked"]["status"] == "failed" and "robots" in items["10.1/blocked"]["reason"])
    check("download: landing page rejected", items["10.1/landing"]["status"] == "failed" and "web page" in items["10.1/landing"]["reason"])
    check("download: truncated PDF rejected", items["10.1/cut"]["status"] == "failed" and "incomplete" in items["10.1/cut"]["reason"])
    check("download: paywalled listed, not fetched", items["10.1/pay"]["status"] == "paywalled")
    check("download: cap respected", items["10.1/many"]["status"] == "skipped")
    user_pdf = Path(tmp) / "Downloads_paper.pdf"
    user_pdf.write_bytes(pdf)
    with contextlib.redirect_stdout(io.StringIO()):
        rc = rt.main(["adopt", str(dest / "manifest.json"), "--file", str(user_pdf), "--doi", "10.1/pay", "--move"])
    items = {i["doi"]: i for i in json.loads((dest / "manifest.json").read_text())["items"]}
    check("adopt: user download filed and moved", rc == 0 and items["10.1/pay"]["status"] == "downloaded by user"
          and (dest / "Lee_2022_Paywalled_paper.pdf").exists() and not user_pdf.exists())
    with contextlib.redirect_stderr(io.StringIO()):
        rc = rt.main(["adopt", str(dest / "manifest.json"), "--file", str(dest / "Lee_2022_Paywalled_paper.pdf"), "--doi", "10.1/pay"])
    check("adopt: refuses a second copy without --replace", rc == 1)
    srv.shutdown()

    # PDF report
    log = json.loads(log_path.read_text())
    log["runs"][0].update(hits=233, source="browser", date="2026-10-17")
    log["chosen"] = {"tier": "balanced", "range": "2021-2026", "reason": "workable size"}
    log["prisma"] = {"excluded_reasons": {"Wrong population": 4}}
    log_path.write_text(json.dumps(log))
    pdf_out = Path(tmp) / "report.pdf"
    p = subprocess.run([sys.executable, str(SCRIPTS / "build_report.py"), "--log", str(log_path), "--records", str(out_path),
                        "--manifest", str(dest / "manifest.json"), "--out", str(pdf_out)], capture_output=True, text=True)
    ok = p.returncode == 0 and pdf_out.read_bytes().startswith(b"%PDF-")
    text = ""
    if ok and shutil.which("pdftotext"):
        text = " ".join(subprocess.run(["pdftotext", str(pdf_out), "-"], capture_output=True, text=True).stdout.split())
    check("report: PDF built", ok, p.stderr[-200:])
    if text:
        check("report: PRISMA boxes with known and unknown numbers",
              "Records identified from" in text and "Duplicate records removed (n = 1)" in text
              and "to be completed" in text and "Wrong population (n = 4)" in text)
        check("report: unread counts say not recorded", "not recorded" in text and "233" in text)


# ---------------------------------------------------------------- screening (the reviewer decides, the script records)
sc = module("screening")


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
        rc = fn(list(args))
    return rc, out.getvalue(), err.getvalue()


with tempfile.TemporaryDirectory() as tmp:
    recs = Path(tmp) / "records.json"
    recs.write_text(json.dumps({"records": [
        {"doi": f"10.9/{i}", "title": f"Paper {i}", "year": 2024, "authors": ["A, B"], "abstract": "x" * 50}
        for i in range(1, 7)]}))
    log = Path(tmp) / "log.json"
    log.write_text(json.dumps({"runs": [], "prisma": {}}))
    rc, out, _ = quiet(sc.main, "batch", str(recs), "--stage", "ta", "--size", "3")
    check("screening: batch shows ids and progress", rc == 0 and "R001" in out and "0 of 6 decided" in out and "R004" not in out)
    rc, _, err = quiet(sc.main, "record", str(recs), "--stage", "ft", "--ids", "R001", "--decision", "include")
    check("screening: full text refused before title/abstract", rc == 1 and "did not pass" in err)
    quiet(sc.main, "record", str(recs), "--stage", "ta", "--ids", "R001-R003", "--decision", "include")
    quiet(sc.main, "record", str(recs), "--stage", "ta", "--ids", "4", "--decision", "exclude", "--reason", "wrong population")
    rc, _, err = quiet(sc.main, "record", str(recs), "--stage", "ta", "--ids", "R099", "--decision", "include")
    check("screening: unknown id rejected", rc == 1 and "R099" in err)
    rc, _, err = quiet(sc.main, "record", str(recs), "--stage", "ta", "--ids", "R005", "--decision", "probably")
    check("screening: unknown decision rejected", rc == 1 and "include, exclude or maybe" in err)
    quiet(sc.main, "prisma", str(recs), "--log", str(log))
    pr = json.loads(log.read_text())["prisma"]
    check("screening: incomplete stage leaves PRISMA boxes empty", pr["screened"] == 6 and pr["screened_excluded"] is None and pr["screened_by"] == "reviewer")
    # spreadsheet route for the rest
    sheet = Path(tmp) / "ta.csv"
    quiet(sc.main, "sheet", str(recs), "--stage", "ta", "--out", str(sheet))
    rows = list(csv.reader(open(sheet, encoding="utf-8-sig")))
    for r in rows[1:]:
        if r[0] == "R005":
            r[1] = "maybe"
        if r[0] == "R006":
            r[1], r[2] = "no", "not empirical"
    with open(sheet, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)
    rc, out, _ = quiet(sc.main, "load", str(recs), "--stage", "ta", str(sheet))
    check("screening: spreadsheet decisions loaded", rc == 0 and "loaded 6" in out)
    tr = Path(tmp) / "to_retrieve.json"
    quiet(sc.main, "included", str(recs), "--stage", "ta", "--out", str(tr))
    check("screening: include and maybe go to full text", len(json.loads(tr.read_text())["records"]) == 4)
    rc, _, err = quiet(sc.main, "record", str(recs), "--stage", "ft", "--ids", "R002", "--decision", "exclude")
    check("screening: full-text exclusion needs a reason", rc == 1 and "needs a reason" in err)
    quiet(sc.main, "record", str(recs), "--stage", "ft", "--ids", "R001,R005", "--decision", "include")
    quiet(sc.main, "record", str(recs), "--stage", "ft", "--ids", "R002", "--decision", "exclude", "--reason", "wrong outcome")
    quiet(sc.main, "record", str(recs), "--stage", "ft", "--ids", "R003", "--decision", "exclude", "--reason", "wrong outcome")
    man = Path(tmp) / "manifest.json"
    man.write_text(json.dumps({"items": [{"doi": "10.9/1", "status": "downloaded"}, {"doi": "10.9/2", "status": "downloaded by user"},
                                         {"doi": "10.9/3", "status": "downloaded"}, {"doi": "10.9/5", "status": "paywalled"}]}))
    quiet(sc.main, "prisma", str(recs), "--log", str(log), "--manifest", str(man))
    pr = json.loads(log.read_text())["prisma"]
    check("screening: PRISMA numbers from recorded decisions",
          (pr["screened"], pr["screened_excluded"], pr["sought"], pr["not_retrieved"], pr["assessed"], pr["included"])
          == (6, 2, 4, 1, 4, 2) and pr["excluded_reasons"] == {"wrong outcome": 2}, json.dumps(pr))
    # report built from a quick-search log with no concepts, plus the reviewer note
    lg = json.loads(log.read_text())
    lg.update(title="Quick search", runs=[{"database": "Google Scholar (web search)", "string": '"gamification" AND motivation',
                                          "hits": 10, "source": "web search", "date": "2026-10-20"}],
              criteria={"Population": "university students", "Years": "2021-2026"})
    log.write_text(json.dumps(lg))
    pdf_out = Path(tmp) / "r.pdf"
    p = subprocess.run([sys.executable, str(SCRIPTS / "build_report.py"), "--log", str(log), "--out", str(pdf_out)], capture_output=True, text=True)
    text = " ".join(subprocess.run(["pdftotext", str(pdf_out), "-"], capture_output=True, text=True).stdout.split()) if p.returncode == 0 and shutil.which("pdftotext") else ""
    check("report: works from a quick-search log", p.returncode == 0, p.stderr[-200:])
    if text:
        check("report: states the reviewer screened", "made by the reviewer" in text and "Eligibility criteria" in text and "Other searches" in text)
        check("report: PRISMA screening numbers", "Records excluded (n = 2)" in text and "wrong outcome (n = 2)" in text and "Reports not retrieved (n = 1)" in text)

# ---------------------------------------------------------------- LRM
with tempfile.TemporaryDirectory() as tmp:
    good = {"title": "T", "papers": [{"title": "A", "authors_year": "Tan (2024)", "quartile": "Unranked/Unavailable",
                                      "method": "Quantitative", "access": "Free", "introduction": "aim",
                                      "methodology": "", "results": "r", "discussion": "d"}]}
    gp, bp = Path(tmp) / "g.json", Path(tmp) / "b.json"
    gp.write_text(json.dumps(good))
    bad = json.loads(json.dumps(good)); bad["papers"][0].update(quartile="Q1-ish guess", method="Survey", access="Open")
    bp.write_text(json.dumps(bad))
    p = subprocess.run([sys.executable, str(SCRIPTS / "build_lrm.py"), str(bp), "--check"], capture_output=True, text=True)
    check("lrm: invalid labels refused", p.returncode == 1 and "quartile" in p.stderr and "method" in p.stderr and "access" in p.stderr)
    out_pdf = Path(tmp) / "lrm.pdf"
    p = subprocess.run([sys.executable, str(SCRIPTS / "build_lrm.py"), str(gp), "--out", str(out_pdf)], capture_output=True, text=True)
    text = " ".join(subprocess.run(["pdftotext", str(out_pdf), "-"], capture_output=True, text=True).stdout.split()) if p.returncode == 0 and shutil.which("pdftotext") else ""
    check("lrm: PDF built", p.returncode == 0, p.stderr[-200:])
    if text:
        check("lrm: empty cells say Not retrieved / Not explicitly stated", "Not retrieved" in text and "Not explicitly stated" in text)

print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
