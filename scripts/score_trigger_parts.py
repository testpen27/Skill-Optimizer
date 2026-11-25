#!/usr/bin/env python3
"""Score run_loop_resilient results per part of the research-matrix skill.

    python3 scripts/score_trigger_parts.py <results-dir> [<results-dir> ...]

Parts come from the "part" field of evals/trigger-eval.json.

Per part: query pass rate (trigger rate >= 0.5 for should-trigger, < 0.5 for
should-not) and run-level accuracy (share of individual probe runs that went
the right way). The 90% bar is checked against both.
"""
import glob
import json
import sys
from pathlib import Path

EVAL = json.load(open(Path(__file__).resolve().parent.parent / "evals" / "trigger-eval.json"))
PART = {e["query"]: e["part"] for e in EVAL}
ORDER = ["LRM", "SYNTHESIS", "CONCEPT", "NON_ACADEMIC", "ADJACENT_ACADEMIC"]


def load(d):
    files = sorted(glob.glob(d.rstrip("/") + "/*/results.json")) or sorted(glob.glob(d.rstrip("/") + "/results.json"))
    if not files:
        sys.exit(f"no results.json under {d}")
    data = json.load(open(files[-1]))
    h = data["history"][-1]
    return (h.get("train_results") or []) + (h.get("test_results") or []), data["history"][-1]["description"]


def score(d):
    res, desc = load(d)
    print(f"\n=== {d.split('/')[-1]}  ({len(res)} queries)")
    print("description:", desc[:140].replace("\n", " "), "...")
    rows = {}
    for r in res:
        p = PART.get(r["query"], "?")
        want = r["should_trigger"]
        right_runs = r["triggers"] if want else r["runs"] - r["triggers"]
        s = rows.setdefault(p, {"q": 0, "qpass": 0, "runs": 0, "right": 0, "fails": []})
        s["q"] += 1
        s["qpass"] += bool(r["pass"])
        s["runs"] += r["runs"]
        s["right"] += right_runs
        if right_runs / r["runs"] < 0.9:
            s["fails"].append((r["triggers"], r["runs"], want, r["query"][:70]))
    allok = True
    print(f"{'part':18} {'queries':>9} {'run-level':>10}  verdict")
    for p in ORDER:
        if p not in rows:
            continue
        s = rows[p]
        qrate, rrate = s["qpass"] / s["q"], s["right"] / s["runs"]
        ok = qrate >= 0.9 and rrate >= 0.9
        allok &= ok
        print(f"{p:18} {s['qpass']:>3}/{s['q']:<3} {qrate:5.0%} {s['right']:>4}/{s['runs']:<4}{rrate:5.0%}  {'PASS' if ok else 'BELOW 90%'}")
        for t, n, want, q in s["fails"]:
            print(f"     weak: triggered {t}/{n} (expected {'yes' if want else 'no'}): {q}")
    print("ALL PARTS >= 90%:", allok)


for d in sys.argv[1:]:
    score(d)
