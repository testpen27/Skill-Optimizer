#!/usr/bin/env python3
"""Put the overclaim pairs the pairing helper found into lrm.json, after checking them.

    python3 apply_overclaims.py lrm.json --from pairing_out/ --papers papers/

pairing_out/<id>.json is the pairing helper's reply for one paper (see
references/overclaim-pairing.md). The reply may carry text around the JSON, or
correct itself with a second JSON object: the LAST object that has an
"overclaims" key is used.

For each flagged pair:
  - the abstract quote and the body quote must both be found in the paper's
    saved text (papers/<id>.txt); a pair with a quote that is not there is dropped;
  - "cell_sentence_id" (for example "results.2") names the sentence of that cell
    to colour; the sentence is looked up in the paper's cell in lrm.json.
    A pair with no usable id is kept as a note on the Summary sheet instead.
Sentences the helper listed as "unsettled" (an abstract claim that might
overclaim but no quote settles it) go to the Summary sheet too.

This replaces any earlier "overclaims" on the papers it processes. Nothing else
in lrm.json changes.
"""

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import json
import os
import sys

from check_evidence import paper_text, quote_found, squash
from common import clean_doi, scrub, split_sentences

TEXT_FIELDS = ["introduction", "methodology", "theory", "results", "discussion"]


def last_object_with(text, key):
    """The last JSON object in `text` that has `key` (a reply may correct itself)."""
    dec, i, found = json.JSONDecoder(), 0, None
    while True:
        j = text.find("{", i)
        if j < 0:
            return found
        try:
            obj, end = dec.raw_decode(text[j:])
        except json.JSONDecodeError:
            i = j + 1
            continue
        if isinstance(obj, dict) and key in obj:
            found = obj
        i = j + end


def reply_file(src, p):
    keys = [k for k in (p.get("id"), clean_doi(p.get("doi")).replace("/", "_") if p.get("doi") else None) if k]
    names = os.listdir(src)
    for k in keys:
        for n in names:
            if n.lower().endswith(".json") and os.path.splitext(n)[0].lower() == k.lower():
                return os.path.join(src, n)
    return None


def locate(p, sid):
    """'results.2' -> (field, the exact sentence) or (None, None)."""
    try:
        field, num = str(sid).rsplit(".", 1)
        sents = split_sentences(p.get(field) or "")
        if field in TEXT_FIELDS and 1 <= int(num) <= len(sents):
            return field, sents[int(num) - 1]
    except (ValueError, AttributeError):
        pass
    return None, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lrm")
    ap.add_argument("--from", dest="src", required=True, help="folder of the pairing helper's replies, <id>.json")
    ap.add_argument("--papers", required=True, help="folder holding each paper's saved text, <id>.txt")
    a = ap.parse_args(argv)
    try:
        data = scrub(json.load(open(a.lrm, encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    placed = noted = dropped = unsettled = missing = 0
    for p in data.get("papers", []):
        tag = p.get("id") or (p.get("title") or "untitled")[:30]
        f = reply_file(a.src, p) if os.path.isdir(a.src) else None
        if not f:
            print(f"{tag}: no pairing reply in {a.src}; left unchanged")
            missing += 1
            continue
        reply = last_object_with(open(f, encoding="utf-8", errors="replace").read(), "overclaims")
        if reply is None:
            print(f"{tag}: no JSON with an \"overclaims\" key in {os.path.basename(f)}; left unchanged")
            missing += 1
            continue
        text, _ = paper_text(a.papers, p)
        text_sq = squash(text) if text else None
        new, notes = [], []
        for oc in reply.get("overclaims") or []:
            ab, body = (oc.get("abstract") or "").strip(), (oc.get("body") or "").strip()
            if not ab or not body:
                dropped += 1
                continue
            if text_sq is None or not (quote_found(ab, text_sq) and quote_found(body, text_sq)):
                print(f"{tag}: DROPPED a pair whose quote is not in the saved text: \"{(ab if text_sq else body)[:70]}\"")
                dropped += 1
                continue
            field, sentence = locate(p, oc.get("cell_sentence_id"))
            entry = {"abstract": ab, "body": body, "body_loc": oc.get("body_loc") or ""}
            if field:
                new.append({"field": field, "text": sentence, **entry})
                placed += 1
            else:
                notes.append(entry)
                noted += 1
        p["overclaims"] = new
        p["overclaims_unplaced"] = notes
        p["overclaims_unsettled"] = [u for u in (reply.get("unsettled") or []) if isinstance(u, str)]
        unsettled += len(p["overclaims_unsettled"])
        print(f"{tag}: {len(new)} coloured, {len(notes)} noted on the Summary sheet, "
              f"{len(p['overclaims_unsettled'])} unsettled")
    with open(a.lrm, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print(f"Done: {placed} coloured, {noted} noted, {dropped} dropped, {unsettled} unsettled "
          f"({missing} paper(s) had no usable reply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
