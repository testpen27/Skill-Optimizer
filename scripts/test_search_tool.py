#!/usr/bin/env python3
"""Regression tests for skills/research-search-string/scripts/search_tool.js.

    python3 scripts/test_search_tool.py

Each case feeds the script a malformed or awkward input and checks that it
fails with a one-line error (exit 1, no stack trace) or builds the right string.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "skills/research-search-string/scripts/search_tool.js"
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

    out_docx = Path(tmp) / "new" / "dir" / "o.docx"
    rc, out, err = run("docx", str(EXAMPLE), str(out_docx))
    check("docx creates the output folder", rc == 0 and out_docx.exists(), err[:120])

    for name, s, kind, want in [
        ("check: curly quotes", "(“OTT” OR Netflix)", "scholar", "curly quotes"),
        ("check: unbalanced brackets", "TITLE-ABS-KEY((a OR b)", "scopus", "unbalanced parentheses"),
        ("check: scholar wildcard", "adopt* AND tv", "scholar", "does not support"),
        ("check: wrong database codes", "TS=(a OR b)", "scopus", "Web of Science field codes"),
        ("check: scholar too long", "a " * 200, "scholar", "256"),
    ]:
        rc, out, _ = run("check", s, kind)
        check(name, want in out, out[-120:])

print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
