#!/usr/bin/env python3
"""Grade the understanding test: python3 grade_uw.py EVALS.json ITERATION_DIR"""
import json, os, re, sys

ev = json.load(open(sys.argv[1]))
it = sys.argv[2]
JOBS = {"strings": ["string"], "fix-string": ["fix", "check", "repair", "debug"], "prisma": ["prisma"],
        "download": ["download", "access"], "lrm": ["lrm", "matrix"], "quick-search": ["quick", "search", "find"]}
MALAY = re.compile(r"\b(anda|saya|kajian|untuk|yang|dan|ini|boleh|dengan|tidak|tahun|carian)\b", re.I)


def norm_jobs(js):
    out = set()
    for j in js or []:
        j = str(j).lower()
        for k, keys in JOBS.items():
            if j == k or any(w in j for w in keys):
                out.add(k)
    if "fix-string" in out and "strings" in out:
        pass
    return out


def questions(text):
    qs = [l.strip() for l in text.splitlines() if "?" in l]
    return qs


rows, total = [], 0
for e in ev:
    d = os.path.join(it, e["id"])
    try:
        u = json.load(open(os.path.join(d, "understanding.json"), encoding="utf-8"))
        reply = open(os.path.join(d, "first_reply.md"), encoding="utf-8").read()
    except Exception as ex:
        rows.append((e["id"], [("ran", False, str(ex))])); continue
    utext = json.dumps(u, ensure_ascii=False).lower() + "\n" + reply.lower()
    checks = []
    got = norm_jobs(u.get("jobs"))
    want = set(e["jobs"])
    if e["id"] == "unclear-goal":
        checks.append(("job: does not commit to a job before asking", not (got - {"quick-search"}) or u.get("will_ask_first"), str(got)))
    else:
        checks.append(("job identified", want <= got or (want == {"fix-string"} and "strings" in got and "fix" in utext), f"want {sorted(want)} got {sorted(got)}"))
    for grp in e.get("keywords", []):
        checks.append((f"keyword kept: {grp[0]}", any(k.lower() in utext for k in grp), ""))
    for grp in e.get("constraints", []):
        checks.append((f"constraint kept: {grp[0]}", any(k.lower() in utext for k in grp), ""))
    qs = questions(reply)
    if e["should_ask"]:
        ok = bool(u.get("will_ask_first")) and re.search(e["ask_about"][0], " ".join(qs), re.I) is not None
        started = re.search(r"TITLE-ABS-KEY\(|\bTS=\(", reply) is not None
        checks.append(("asks the right clarifying question before working", ok and not started, " | ".join(qs)[:200]))
        n_q = len(u.get("questions") or [])
        checks.append(("asks three questions or fewer", n_q <= 3, f"{n_q} questions: " + " | ".join(map(str, u.get("questions") or []))[:220]))
        if e.get("also_ask"):
            checks.append(("asks the specific ambiguity (question or its options)", bool(u.get("will_ask_first")) and re.search(e["also_ask"], reply, re.I) is not None, " | ".join(qs)[:200]))
    else:
        bad = [q for q in qs if e.get("must_not_ask") and re.search(e["must_not_ask"], q, re.I)]
        checks.append(("does not re-ask what the user already said", not bad, " | ".join(bad)[:200]))
    for db in e.get("must_not_plan_databases", []):
        dbs = " ".join(map(str, u.get("databases") or [])).lower()
        checks.append((f"does not plan {db}", db not in dbs, dbs))
    for j in e.get("must_not_plan_jobs", []):
        checks.append((f"does not plan {j}", j not in got, str(got)))
    if e.get("reply_language") == "ms":
        checks.append(("replies in the user's language (Malay)", len(MALAY.findall(reply)) >= 8, f"{len(MALAY.findall(reply))} Malay function words"))
    rows.append((e["id"], checks))

passed = sum(c[1] for _, cs in rows for c in cs); n = sum(len(cs) for _, cs in rows)
for rid, cs in rows:
    p = sum(c[1] for c in cs)
    print(f"{rid:20} {p}/{len(cs)}")
    for name, ok, ev_ in cs:
        if not ok:
            print(f"    FAIL {name} :: {ev_}")
print(f"TOTAL {passed}/{n}")
json.dump({rid: [{"text": a, "passed": b, "evidence": c} for a, b, c in cs] for rid, cs in rows},
          open(os.path.join(it, "grading.json"), "w"), indent=1)
