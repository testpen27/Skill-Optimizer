#!/usr/bin/env python3
"""Grade iteration-1 runs: writes grading.json (text/passed/evidence) per run."""
import glob
import json
import os
import re
import subprocess
import sys

WS = os.path.dirname(os.path.abspath(__file__))
IT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WS, "iteration-1")


def read_all(out, exts=(".md", ".txt", ".json", ".csv")):
    text = ""
    for p in glob.glob(os.path.join(out, "**", "*"), recursive=True):
        if os.path.isfile(p) and p.endswith(exts) and "/papers/" not in p:
            try:
                text += f"\n### {os.path.relpath(p, out)}\n" + open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                pass
    return text


def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout


def a(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": evidence[:400]}


def grade_strings(out):
    allt = read_all(out)
    resp = open(os.path.join(out, "response.md"), encoding="utf-8").read() if os.path.exists(os.path.join(out, "response.md")) else ""
    q = open(os.path.join(out, "questions.md"), encoding="utf-8").read() if os.path.exists(os.path.join(out, "questions.md")) else ""
    r = []
    r.append(a("Asked for the field and the year range(s) before writing strings",
               q and re.search(r"field|discipline", q, re.I) and re.search(r"year", q, re.I),
               q[:300] or "no questions.md"))
    r.append(a("Scopus strings for both 2016-2020 and 2021-2026",
               "PUBYEAR > 2015 AND PUBYEAR < 2021" in allt and "PUBYEAR > 2020 AND PUBYEAR < 2027" in allt,
               "found" if "PUBYEAR > 2015" in allt else "missing 2016-2020 Scopus limit"))
    r.append(a("Web of Science strings for both ranges",
               "PY=(2016-2020)" in allt and "PY=(2021-2026)" in allt, "checked PY=(...)"))
    tiers = [t for t in ("broad", "balanced", "narrow") if re.search(rf"\b{t}\b", allt, re.I)]
    r.append(a("More than one tier (broad / balanced / narrow) offered", len(tiers) >= 2, f"tiers seen: {tiers}"))
    r.append(a("Malaysia niche in the strings", re.search(r"Malaysia", allt) is not None, "searched outputs"))
    claimed = re.search(r"(returned|found|gives?|got)\s+[\d,]{2,}\s+(results|documents|records|hits)", resp, re.I)
    r.append(a("Does not claim hit counts it never read", not claimed, claimed.group(0) if claimed else "no hit-count claims"))
    return r


def find_decisions(out):
    """Return {id: (decision, reason)} from any JSON or CSV in the folder."""
    found = {}
    for p in glob.glob(os.path.join(out, "**", "*.json"), recursive=True):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        for rec in (d.get("records") if isinstance(d, dict) else None) or []:
            rid = rec.get("id")
            sc = rec.get("screening") or {}
            # pre-research nests by stage; a hand-rolled record may keep one flat entry
            s = sc.get("title_abstract") or (sc if "decision" in sc else None) or rec.get("ta_decision") or rec.get("decision")
            if rid and s:
                if isinstance(s, dict):
                    found[rid] = (s.get("decision", ""), s.get("reason", ""))
                else:
                    found[rid] = (str(s), rec.get("reason", ""))
    if not found:  # fall back to any table mentioning the ids
        text = read_all(out, (".csv", ".md", ".json"))
        for rid in ("R001", "R002", "R003", "R004", "R005"):
            m = re.search(rf"{rid}[^\n]*?\b(include|exclude|maybe)\b", text, re.I)
            if m:
                found[rid] = (m.group(1).lower(), "")
    return found


def grade_screening(out):
    dec = find_decisions(out)
    want = {"R001": "include", "R002": "include", "R003": "exclude", "R004": "maybe", "R005": "exclude"}
    resp = open(os.path.join(out, "response.md"), encoding="utf-8").read() if os.path.exists(os.path.join(out, "response.md")) else ""
    log = {}
    if os.path.exists(os.path.join(out, "search_log.json")):
        log = json.load(open(os.path.join(out, "search_log.json"), encoding="utf-8"))
    pr = log.get("prisma") or {}
    r = []
    ok = all(dec.get(k, ("",))[0].lower().startswith(v) for k, v in want.items())
    r.append(a("All five decisions recorded in the project files exactly as the reviewer gave them", ok, json.dumps(dec)))
    reasons = all(dec.get(k, ("", ""))[1] for k in ("R003", "R005"))
    r.append(a("Exclusion reasons recorded for R003 and R005", reasons, json.dumps({k: dec.get(k) for k in ("R003", "R005")})))
    r.append(a("R004 left as 'maybe' (not decided by Claude)", dec.get("R004", ("",))[0].lower().startswith("maybe"), str(dec.get("R004"))))
    nums = (re.search(r"\b5\b", resp) and re.search(r"\b2\b", resp) and re.search(r"\b3\b", resp))
    r.append(a("Reports screened 5, excluded 2, going to full text 3",
               bool(nums) or (pr.get("screened") == 5 and pr.get("screened_excluded") == 2 and pr.get("sought") == 3),
               json.dumps({k: pr.get(k) for k in ("screened", "screened_excluded", "sought")}) + " | " + resp[:200]))
    invented = pr.get("included") not in (None, "") or re.search(r"(studies )?included in (the )?review[^\n]{0,20}\b\d+\b", resp, re.I)
    r.append(a("Does not invent later PRISMA numbers (full text, included)", not invented, json.dumps({k: pr.get(k) for k in ("assessed", "included")})))
    r.append(a("Makes clear the decisions were the reviewer's",
               re.search(r"your (decisions?|screening)|as you (gave|decided)|reviewer", resp, re.I) is not None, resp[:200]))
    return r


def grade_lrm(out):
    pdfs = [p for p in glob.glob(os.path.join(out, "**", "*.pdf"), recursive=True)]
    r = []
    if not pdfs:
        return [a("LRM PDF produced", False, "no PDF")]
    pdf = pdfs[0]
    txt = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout  # reading order, not layout
    flat = " ".join(txt.split())
    table = re.split(r"\bSynthesis\b", flat, maxsplit=1)[0]  # labels live in the table, not in advice below it
    info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", info)
    landscape = m and float(m.group(1)) > float(m.group(2))
    r.append(a("LRM PDF produced, landscape", landscape, f"{os.path.basename(pdf)} {m.group(0) if m else info[:80]}"))
    titles = ["Gamified quizzes", "Leaderboards", "lived experience", "Badges and engagement"]
    r.append(a("All four papers in the matrix", all(t.lower() in flat.lower() for t in titles), str([t for t in titles if t.lower() not in flat.lower()])))
    fake_q = re.search(r"\bQ[1-4]\b", table)
    r.append(a("No quartile invented for journals that cannot be looked up", not fake_q, fake_q.group(0) if fake_q else "no Q1-Q4 in PDF"))
    r.append(a("Thesis marked N/A for quartile", re.search(r"N/\s?A", flat) is not None, "searched for N/A"))
    r.append(a("Missing results shown as not retrieved, not invented", re.search(r"not\s+retrieved|not\s+available|missing", flat, re.I) is not None, "searched PDF"))
    r.append(a("Missing framework shown as not stated", re.search(r"not\s+(explicitly\s+)?stated", flat, re.I) is not None, "searched PDF"))
    labels = re.findall(r"\b(Free|Paid|Unclear)\b", table)
    r.append(a("Access marked Unclear (no evidence of free or paid)", labels and all(l == "Unclear" for l in labels), str(labels)))
    return r


GRADERS = {"strings-intake-tiers-ranges": grade_strings, "prisma-record-reviewer-screening": grade_screening,
           "lrm-from-four-papers": grade_lrm}

for d in sorted(glob.glob(os.path.join(IT, "eval-*"))):
    name = os.path.basename(d)[5:]
    for cfg in ("with_skill", "old_skill"):
        out = os.path.join(d, cfg, "outputs")
        if not os.path.exists(os.path.join(out, "response.md")):
            print(f"{name}/{cfg}: not finished")
            continue
        exp = GRADERS[name](out)
        passed = sum(e["passed"] for e in exp)
        json.dump({"expectations": exp, "summary": {"passed": passed, "failed": len(exp) - passed, "total": len(exp),
                                                   "pass_rate": round(passed / len(exp), 3)}},
                  open(os.path.join(d, cfg, "grading.json"), "w"), indent=1)
        print(f"{name}/{cfg}: {passed}/{len(exp)}")
        for e in exp:
            if not e["passed"]:
                print("   FAIL", e["text"], "|", e["evidence"][:150])
