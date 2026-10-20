#!/usr/bin/env python3
"""Record the reviewer's screening decisions and turn them into PRISMA numbers.

The reviewer makes every decision. Claude shows records, writes down what the
reviewer said, and counts. Standard library only.

Stages: ta (title and abstract) and ft (full text).

  batch    records.json --stage ta [--size 20]     show the next undecided records
  record   records.json --stage ta --ids R001,R004-R009 --decision exclude [--reason "..."]
  sheet    records.json --stage ta --out screening.csv     spreadsheet for the reviewer
  load     records.json --stage ta screening.csv           read the filled spreadsheet back
  included records.json --stage ta --out to_retrieve.json  records that go on to the next stage
  status   records.json
  prisma   records.json --log search_log.json [--manifest papers/manifest.json]

Decisions: include, exclude, maybe. At the full-text stage an exclusion needs a
reason, because PRISMA reports full-text exclusions by reason. "maybe" at the
title-and-abstract stage goes on to full text, as is usual.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter

STAGES = {"ta": "title_abstract", "ft": "full_text"}
DECISIONS = {"include": "include", "in": "include", "i": "include", "yes": "include", "y": "include",
             "exclude": "exclude", "ex": "exclude", "e": "exclude", "no": "exclude", "n": "exclude",
             "maybe": "maybe", "m": "maybe", "unsure": "maybe", "?": "maybe"}


class Fail(Exception):
    pass


def load(path):
    try:
        data = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        raise Fail(f"cannot find {path}")
    except json.JSONDecodeError as e:
        raise Fail(f"{path} is not valid JSON ({e})")
    if "records" not in data:
        raise Fail(f"{path} has no records list")
    for i, r in enumerate(data["records"], 1):
        r.setdefault("id", f"R{i:03d}")
        r.setdefault("screening", {})
    return data


def save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def stage_name(s):
    if s not in STAGES:
        raise Fail("stage must be ta (title and abstract) or ft (full text)")
    return STAGES[s]


def in_stage(data, stage):
    """Records that reach this stage: all of them for ta; ta include/maybe for ft."""
    if stage == "title_abstract":
        return data["records"]
    return [r for r in data["records"] if r["screening"].get("title_abstract", {}).get("decision") in ("include", "maybe")]


def parse_ids(spec, known):
    ids = []
    for part in re.split(r"[,\s]+", spec.strip()):
        if not part:
            continue
        m = re.fullmatch(r"R?(\d+)\s*-\s*R?(\d+)", part, re.I)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a > b:
                a, b = b, a
            ids += [f"R{n:03d}" for n in range(a, b + 1)]
        elif re.fullmatch(r"R?\d+", part, re.I):
            ids.append(f"R{int(part.lstrip('Rr')):03d}")
        else:
            raise Fail(f"cannot read the id {part!r}; use forms like R004, 4 or R004-R009")
    unknown = [i for i in ids if i not in known]
    if unknown:
        raise Fail(f"no record with id {', '.join(unknown[:5])}")
    return ids


def decide(r, stage, decision, reason):
    d = DECISIONS.get((decision or "").strip().lower())
    if not d:
        raise Fail(f"decision must be include, exclude or maybe, not {decision!r}")
    if stage == "full_text" and d == "exclude" and not (reason or "").strip():
        raise Fail(f"{r['id']}: a full-text exclusion needs a reason (PRISMA reports them by reason)")
    r["screening"][stage] = {"decision": d, "reason": (reason or "").strip(), "by": "reviewer",
                             "date": time.strftime("%Y-%m-%d")}


def cmd_batch(a):
    data = load(a.records)
    stage = stage_name(a.stage)
    pool = in_stage(data, stage)
    todo = [r for r in pool if stage not in r["screening"]]
    print(f"{len(pool) - len(todo)} of {len(pool)} decided at the {stage.replace('_', ' ')} stage.\n")
    for r in todo[: a.size]:
        authors = "; ".join((r.get("authors") or [])[:3])
        print(f"{r['id']}  {r.get('title') or '(no title)'}")
        print(f"      {authors} ({r.get('year') or 'n.d.'}). {r.get('venue') or ''}")
        abstract = (r.get("abstract") or "").strip()
        print("      " + (abstract[:700] + ("..." if len(abstract) > 700 else "") if abstract else "(no abstract in the export)"))
        print()
    save(a.records, data)  # keeps the ids stable from the first look onwards


def cmd_record(a):
    data = load(a.records)
    stage = stage_name(a.stage)
    allowed = {r["id"]: r for r in in_stage(data, stage)}
    known = {r["id"] for r in data["records"]}
    ids = parse_ids(a.ids, known)
    outside = [i for i in ids if i not in allowed]
    if outside:
        raise Fail(f"{', '.join(outside[:5])} did not pass title-and-abstract screening, so they are not at the full-text stage")
    for i in ids:
        decide(allowed[i], stage, a.decision, a.reason)
    save(a.records, data)
    print(f"recorded {a.decision} for {len(ids)} record(s) at the {stage.replace('_', ' ')} stage")


def cmd_sheet(a):
    data = load(a.records)
    stage = stage_name(a.stage)
    with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "decision (include/exclude/maybe)", "reason", "title", "authors", "year", "venue", "doi", "abstract"])
        for r in in_stage(data, stage):
            prev = r["screening"].get(stage, {})
            w.writerow([r["id"], prev.get("decision", ""), prev.get("reason", ""), r.get("title", ""),
                        "; ".join(r.get("authors") or []), r.get("year") or "", r.get("venue", ""), r.get("doi", ""),
                        r.get("abstract", "")])
    save(a.records, data)
    print(f"wrote {a.out}: fill the decision and reason columns, then load it back")


def cmd_load(a):
    data = load(a.records)
    stage = stage_name(a.stage)
    allowed = {r["id"]: r for r in in_stage(data, stage)}
    problems, done = [], 0
    with open(a.sheet, newline="", encoding="utf-8-sig") as f:
        for n, row in enumerate(csv.reader(f), 1):
            if n == 1 or not row or not row[0].strip():
                continue
            rid, decision = row[0].strip(), (row[1] if len(row) > 1 else "").strip()
            reason = row[2].strip() if len(row) > 2 else ""
            if not decision:
                continue
            if rid not in allowed:
                problems.append(f"row {n}: {rid} is not at this stage")
                continue
            try:
                decide(allowed[rid], stage, decision, reason)
                done += 1
            except Fail as e:
                problems.append(f"row {n}: {e}")
    save(a.records, data)
    print(f"loaded {done} decision(s)")
    if problems:
        print("not loaded:\n- " + "\n- ".join(problems[:20]))
        return 1
    return 0


def cmd_included(a):
    data = load(a.records)
    stage = stage_name(a.stage)
    pool = in_stage(data, stage)
    pending = [r["id"] for r in pool if stage not in r["screening"]]
    if pending:
        print(f"warning: {len(pending)} record(s) not yet decided at this stage, left out: {', '.join(pending[:10])}", file=sys.stderr)
    keep = [r for r in pool if r["screening"].get(stage, {}).get("decision") in ("include", "maybe")]
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"records": keep}, f, indent=2, ensure_ascii=False)
    print(f"{len(keep)} record(s) -> {a.out}")


def progress(data):
    out = {}
    for stage in STAGES.values():
        pool = in_stage(data, stage)
        c = Counter(r["screening"].get(stage, {}).get("decision", "undecided") for r in pool)
        out[stage] = (len(pool), c)
    return out


def cmd_status(a):
    data = load(a.records)
    for stage, (n, c) in progress(data).items():
        print(f"{stage.replace('_', ' ')}: {n} record(s); " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())))


def cmd_prisma(a):
    data = load(a.records)
    log = json.load(open(a.log, encoding="utf-8"))
    pr = log.setdefault("prisma", {})
    prog = progress(data)
    n_ta, c_ta = prog["title_abstract"]
    n_ft, c_ft = prog["full_text"]
    pr["screened_by"] = "reviewer"
    pr["screened"] = n_ta
    notes = []
    if c_ta.get("undecided"):
        notes.append(f"title-and-abstract screening incomplete: {c_ta['undecided']} of {n_ta} undecided")
        for k in ("screened_excluded", "sought", "not_retrieved", "assessed", "included", "included_reports"):
            pr[k] = None
        pr["excluded_reasons"] = {}
    else:
        pr["screened_excluded"] = c_ta.get("exclude", 0)
        pr["sought"] = n_ft
        retrieved = None
        if a.manifest and os.path.exists(a.manifest):
            items = {i.get("doi"): i for i in json.load(open(a.manifest, encoding="utf-8")).get("items", [])}
            got = [r for r in in_stage(data, "full_text")
                   if items.get(r.get("doi"), {}).get("status", "").startswith("downloaded")]
            retrieved = len(got)
            pr["not_retrieved"] = n_ft - retrieved
        else:
            notes.append("no manifest given, so reports not retrieved is unknown")
            pr["not_retrieved"] = None
        decided_ft = n_ft - c_ft.get("undecided", 0)
        if c_ft.get("undecided"):
            notes.append(f"full-text screening incomplete: {c_ft['undecided']} of {n_ft} undecided")
            pr["assessed"] = decided_ft or None
            pr["included"] = None
            pr["included_reports"] = None
        else:
            pr["assessed"] = decided_ft
            pr["included"] = c_ft.get("include", 0)
            pr["included_reports"] = c_ft.get("include", 0)
        reasons = Counter(r["screening"]["full_text"]["reason"] for r in in_stage(data, "full_text")
                          if r["screening"].get("full_text", {}).get("decision") == "exclude")
        pr["excluded_reasons"] = dict(reasons.most_common())
        if c_ft.get("maybe"):
            notes.append(f"{c_ft['maybe']} full-text decision(s) are still 'maybe'; resolve them before the final diagram")
    with open(a.log, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: v for k, v in pr.items()}, indent=1))
    for n in notes:
        print("note:", n)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("batch"); p.add_argument("records"); p.add_argument("--stage", required=True)
    p.add_argument("--size", type=int, default=20); p.set_defaults(fn=cmd_batch)
    p = sub.add_parser("record"); p.add_argument("records"); p.add_argument("--stage", required=True)
    p.add_argument("--ids", required=True); p.add_argument("--decision", required=True)
    p.add_argument("--reason", default=""); p.set_defaults(fn=cmd_record)
    p = sub.add_parser("sheet"); p.add_argument("records"); p.add_argument("--stage", required=True)
    p.add_argument("--out", required=True); p.set_defaults(fn=cmd_sheet)
    p = sub.add_parser("load"); p.add_argument("records"); p.add_argument("--stage", required=True)
    p.add_argument("sheet"); p.set_defaults(fn=cmd_load)
    p = sub.add_parser("included"); p.add_argument("records"); p.add_argument("--stage", required=True)
    p.add_argument("--out", required=True); p.set_defaults(fn=cmd_included)
    p = sub.add_parser("status"); p.add_argument("records"); p.set_defaults(fn=cmd_status)
    p = sub.add_parser("prisma"); p.add_argument("records"); p.add_argument("--log", required=True)
    p.add_argument("--manifest"); p.set_defaults(fn=cmd_prisma)
    a = ap.parse_args(argv)
    try:
        return a.fn(a) or 0
    except Fail as e:
        print("Error:", e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
