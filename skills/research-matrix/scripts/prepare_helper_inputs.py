#!/usr/bin/env python3
"""Build the input files that pairing, verification and gap helpers read, from lrm.json.

    python3 prepare_helper_inputs.py lrm.json --kind pairing --out pairing_in/
    python3 prepare_helper_inputs.py lrm.json --kind verify  --out verify_in/
    python3 prepare_helper_inputs.py lrm.json --kind gaps    --out gaps_in/ --title "Research title"

pairing and verify write one <id>.json per paper (the formats in
references/overclaim-pairing.md and references/verifier-prompt.md); gaps writes
one gap_input.json for the whole set (references/gap-list.md). The session never
re-types these: that costs output tokens and is a chance to change a word.
"""

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import json
import os
import sys

from common import clean_doi, fold, scrub, split_sentences

COLS = ["introduction", "methodology", "theory", "results", "discussion", "limitations"]
PAIR_COLS = COLS[:5]


def q_of(item):
    return (item.get("q") if isinstance(item, dict) else str(item)).strip()


def pid(p):
    return p.get("id") or clean_doi(p.get("doi")).replace("/", "_") or fold(p.get("title") or "")[:30]


def sentences(p, cols):
    out = []
    for c in cols:
        for k, s in enumerate(split_sentences(p.get(c) or ""), 1):
            out.append({"id": f"{c}.{k}", "sentence": s})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lrm")
    ap.add_argument("--kind", required=True, choices=["pairing", "verify", "gaps"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="")
    a = ap.parse_args(argv)
    try:
        data = scrub(json.load(open(a.lrm, encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    os.makedirs(a.out, exist_ok=True)
    papers = data.get("papers") or []
    n = 0
    if a.kind == "gaps":
        obj = {"title": a.title or data.get("title") or "",
               "papers": [{"id": pid(p), "year": p.get("year"), "type": p.get("type"),
                           "methodology": p.get("methodology") or "Not retrieved",
                           "limitations": p.get("limitations") or "Not explicitly stated"} for p in papers]}
        json.dump(obj, open(os.path.join(a.out, "gap_input.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"wrote gap_input.json ({len(papers)} papers)")
        return 0
    for p in papers:
        ev = p.get("evidence") or {}
        if a.kind == "pairing":
            claims = [q_of(x) for x in p.get("abstract_claims") or []]
            if not claims:
                continue
            obj = {"abstract_claims": claims,
                   "body_quotes": {"caveats": [q_of(x) for x in p.get("caveats") or []],
                                   "results_evidence": [q_of(x) for x in ev.get("results") or []],
                                   "discussion_evidence": [q_of(x) for x in ev.get("discussion") or []]},
                   "cell_sentences": sentences(p, PAIR_COLS)}
        else:
            sents = sentences(p, COLS)
            if not sents:
                continue
            obj = {"sentences": sents,
                   "quotes": {c: [q_of(x) for x in ev.get(c) or []] for c in COLS if p.get(c)},
                   "overclaims": [{"id": f"overclaim.{k}", "field": oc.get("field"), "abstract": oc.get("abstract"),
                                   "body": oc.get("body"), "cell_text": oc.get("text")}
                                  for k, oc in enumerate(p.get("overclaims") or [], 1)]}
        json.dump(obj, open(os.path.join(a.out, f"{pid(p)}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        n += 1
    print(f"wrote {n} {a.kind} input file(s) to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
