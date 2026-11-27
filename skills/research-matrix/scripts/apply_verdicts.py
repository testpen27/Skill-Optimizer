#!/usr/bin/env python3
"""Apply the verifier's verdicts to lrm.json.

    python3 apply_verdicts.py lrm.json --from verify_out/ [--narrow report|trim|drop]

verify_out/<id>.json is the verification helper's reply for one paper
(references/verifier-prompt.md): {"verdicts": [{"id": "results.2", "verdict":
"keep|cut|narrow", "reason": "...", "support": "..."}]}; the LAST object with a
"verdicts" key is used. Ids are "<column>.<n>" (a sentence of that cell) or
"overclaim.<n>" (the n-th recorded overclaim).

  keep    nothing changes
  cut     the sentence is removed from its cell (an overclaim: removed)
  narrow  with --narrow trim only the unsupported words the verifier named ("support") are
          removed from the sentence (several places may be separated by ";" or "|"; an ellipsis ("...") means one phrase with words skipped, so the sentence goes whole; the seams
          are mended: no doubled commas, no ", and." or "used and X"; a sentence that is then under
          3 words, ends or begins as a fragment, or whose words are not found in it, is removed whole); with --narrow drop the whole sentence is removed;
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
import re
import sys

from apply_overclaims import last_object_with, reply_file
from common import scrub, split_sentences

COLS = ["introduction", "methodology", "theory", "results", "discussion", "limitations"]

# Words a sentence cannot end on, or start with: what is left after a removal is a fragment.
_DANGLING_END = {"was", "were", "is", "are", "will", "be", "been", "that", "of", "to", "the", "a", "an", "and",
                 "or", "with", "by", "in", "on", "for", "as", "include", "includes", "including", "used",
                 "than", "from", "at", "which", "who", "but"}
_LEAD_CONJ = ("and ", "or ", "but ")


def tidy(t):
    """Mend the seams a removal leaves (doubled commas, ', and.', 'used and X') without adding a word.
    Returns the sentence, or "" when what is left is a fragment, which the caller drops whole."""
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    t = re.sub(r"\bthat,\s*(?:and|or) that\b", "that", t)
    t = re.sub(r"[,;]\s*(?=[,;])", "", t)                      # ",," -> ","
    t = re.sub(r"[,;]?\s*\b(?:and|or|but)(?:\s+that)?\s*(?=[.!?]?$)", "", t)   # trailing ", and." / " and that."
    t = re.sub(r",\s*(?=[.!?]$)", "", t)                       # ",." -> "."
    t = re.sub(r"\b(that|include|includes|including|used|by|of|with|to|in|on|for|as|were|was|is|are)\s+(?:and|or)\s+",
               r"\1 ", t)                                      # "used and X" -> "used X"
    t = t.strip(" ,;")
    words = re.sub(r"[.!?]+$", "", t).split()
    if not words or words[-1].lower() in _DANGLING_END or t.lower().startswith(_LEAD_CONJ):
        return ""
    return t


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lrm")
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--narrow", choices=["report", "trim", "drop"], default="report")
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
                elif how == "narrow" and a.narrow == "trim":
                    sup = (v.get("support") or "").strip()
                    if sup and sup in s:
                        parts = [sup]
                    elif re.search(r"\.\.\.|\u2026", sup):
                        parts = []     # an ellipsis is one phrase with words skipped: no clean cut, drop the sentence
                    else:              # the verifier may name several separate places: "x; y" or "x | y"
                        parts = [x.strip(" ,") for x in re.split(r"\s*[;|]\s*", sup)]
                        parts = [x for x in parts if x and x in s]
                    t = s
                    for x in parts:
                        t = t.replace(x, "", 1)
                    t = tidy(t) if parts else ""
                    tot["narrow"] += 1
                    if len(t.split()) >= 3:
                        keep.append(t if t[-1] in ".!?" else t + ".")
                        todo.append(f'{name} {c}.{k} TRIMMED (reread it): removed "{sup}"')
                    else:
                        todo.append(f'{name} {c}.{k} DROPPED whole (nothing usable left after removing "{sup}")')
                    continue
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
            if keep != sents:          # a removed sentence, or one trimmed in place
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
