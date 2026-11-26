#!/usr/bin/env python3
"""Apply the verifier's verdicts to lrm.json.

    python3 apply_verdicts.py lrm.json --from verify_out/ [--narrow report|drop]

verify_out/<id>.json is the verification helper's reply for one paper
(references/verifier-prompt.md): {"verdicts": [{"id": "results.2", "verdict":
"keep|cut|narrow", "reason": "...", "support": "..."}]}; the LAST object with a
"verdicts" key is used. Ids are "<column>.<n>" (a sentence of that cell) or
"overclaim.<n>" (the n-th recorded overclaim).

  keep    nothing changes
  cut     the sentence is removed from its cell (an overclaim: removed)
  narrow  with --narrow drop the whole sentence is removed (safe: nothing is added);
          with --narrow report (default) nothing changes and the sentence is listed,
          with the unsupported words, for the session to rewrite closer to the quotes
A sentence or overclaim with no verdict was not verified: it is listed, not changed.
Only removal happens here; this script never writes new words into a cell.
"""

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import json
import os
import sys

from apply_overclaims import last_object_with, reply_file
from common import scrub, split_sentences

COLS = ["introduction", "methodology", "theory", "results", "discussion", "limitations"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lrm")
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--narrow", choices=["report", "drop"], default="report")
    a = ap.parse_args(argv)
    try:
        data = json.load(open(a.lrm, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    if not os.path.isdir(a.src):
        print(f"Error: {a.src} is not a folder", file=sys.stderr)
        return 1
    tot = {"keep": 0, "cut": 0, "narrow": 0, "unverified": 0, "no reply": 0}
    todo = []
    for p in data.get("papers") or []:
        name = p.get("id") or ""
        f = reply_file(a.src, p)
        if not f:
            tot["no reply"] += 1
            todo.append(f"{name}: no verifier reply found")
            continue
        obj = last_object_with(open(f, encoding="utf-8", errors="replace").read(), "verdicts")
        if not obj:
            tot["no reply"] += 1
            todo.append(f"{name}: reply has no verdicts")
            continue
        vs = {str(v.get("id")): v for v in obj["verdicts"] if isinstance(v, dict)}
        for c in COLS:
            sents = split_sentences(p.get(c) or "")
            keep = []
            for k, s in enumerate(sents, 1):
                v = vs.get(f"{c}.{k}")
                how = (v or {}).get("verdict")
                if how == "keep":
                    tot["keep"] += 1
                elif how == "cut" or (how == "narrow" and a.narrow == "drop"):
                    tot["cut" if how == "cut" else "narrow"] += 1
                    continue
                elif how == "narrow":
                    tot["narrow"] += 1
                    todo.append(f'{name} {c}.{k} NARROW: remove "{v.get("support", "")}" ({v.get("reason", "")})')
                else:
                    tot["unverified"] += 1
                    todo.append(f"{name} {c}.{k}: no verdict, not verified")
                keep.append(s)
            if len(keep) != len(sents):
                p[c] = " ".join(keep)
        ocs = []
        for k, oc in enumerate(p.get("overclaims") or [], 1):
            v = vs.get(f"overclaim.{k}")
            if v and v.get("verdict") == "cut":
                tot["cut"] += 1
                continue
            if not v:
                tot["unverified"] += 1
            ocs.append(oc)
        if "overclaims" in p:
            p["overclaims"] = [oc for oc in ocs if (oc.get("text") or "").strip() in (p.get(oc.get("field")) or "")]
    json.dump(scrub(data), open(a.lrm, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"verdicts applied: {tot}")
    for t in todo:
        print("TO DO: " + t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
