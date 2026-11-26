#!/usr/bin/env python3
"""Put the checked research-gap list into lrm.json.

    python3 apply_gaps.py lrm.json --gaps gaps_out/gaps.json --verdicts gaps_check/verdicts.json

gaps.json is the writing helper's reply (references/gap-list.md): a JSON object
with a "gaps" list of {"gap", "kind", "papers", "basis"}. verdicts.json is the
checking helper's reply: {"verdicts": [{"id": "gap.1", "verdict":
"keep|narrow|cut", "reason": "...", "narrowed": "rewritten gap (for narrow)"}]}.
Either reply may carry text around the JSON, or correct itself with a second
object: the LAST object with the right key is used.

  keep    the gap goes in as written
  narrow  the gap goes in with the checker's "narrowed" text (no text: dropped)
  cut     the gap is dropped
A gap with no verdict was not checked and is dropped. Papers are named by id or
DOI; one that is not in lrm.json is removed from the gap, and a gap left with
no paper is dropped. Without --verdicts nothing is written, unless
--unchecked is given (the Summary sheet then carries gaps nobody checked: say so).

This replaces any earlier "gaps" in lrm.json. Nothing else changes.
"""

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import json
import sys

from apply_overclaims import last_object_with
from common import is_pcode, resolve_paper, scrub

KINDS = {"stated by authors", "across papers"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lrm")
    ap.add_argument("--gaps", required=True, help="the writing helper's reply (JSON file)")
    ap.add_argument("--verdicts", help="the checking helper's reply (JSON file)")
    ap.add_argument("--unchecked", action="store_true", help="write the gaps without a check (not recommended)")
    a = ap.parse_args(argv)
    if not a.verdicts and not a.unchecked:
        print("Error: no --verdicts. A gap is written only after the checker has seen it "
              "(use --unchecked to override and say so to the user).", file=sys.stderr)
        return 1
    try:
        data = json.load(open(a.lrm, encoding="utf-8"))
        written = last_object_with(open(a.gaps, encoding="utf-8").read(), "gaps")
        checked = last_object_with(open(a.verdicts, encoding="utf-8").read(), "verdicts") if a.verdicts else None
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    if not written or not isinstance(written.get("gaps"), list):
        print(f'Error: {a.gaps} has no JSON object with a "gaps" list', file=sys.stderr)
        return 1
    if a.verdicts and not checked:
        print(f'Error: {a.verdicts} has no JSON object with a "verdicts" list', file=sys.stderr)
        return 1
    verdict = {str(v.get("id")): v for v in (checked or {}).get("verdicts", []) if isinstance(v, dict)}
    src = [{"code": f"P{i:02d}", "id": p.get("id"), "doi": p.get("doi")} for i, p in enumerate(data.get("papers") or [], 1)]
    kept, counts = [], {"keep": 0, "narrow": 0, "cut": 0, "unchecked": 0, "no paper": 0, "bad": 0}
    for i, g in enumerate(written["gaps"], 1):
        if not isinstance(g, dict) or not (g.get("gap") or "").strip() or g.get("kind") not in KINDS:
            counts["bad"] += 1
            continue
        text, how = g["gap"].strip(), "keep"
        if a.verdicts:
            v = verdict.get(f"gap.{i}")
            if not v:
                counts["unchecked"] += 1
                continue
            how = v.get("verdict")
            if how == "cut" or (how == "narrow" and not (v.get("narrowed") or "").strip()):
                counts["cut"] += 1
                continue
            if how == "narrow":
                text = v["narrowed"].strip()
            elif how != "keep":
                counts["bad"] += 1
                continue
        papers = [k for k in g.get("papers") or [] if not is_pcode(k) and resolve_paper(k, src)]
        if not papers:
            counts["no paper"] += 1
            continue
        counts[how] += 1
        kept.append({"gap": text, "kind": g["kind"], "papers": papers, "basis": (g.get("basis") or "").strip()})
    data["gaps"] = scrub(kept)
    json.dump(data, open(a.lrm, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"gaps written: {len(kept)}  (kept {counts['keep']}, narrowed {counts['narrow']}, cut {counts['cut']}, "
          f"unchecked {counts['unchecked']}, no paper left {counts['no paper']}, malformed {counts['bad']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
