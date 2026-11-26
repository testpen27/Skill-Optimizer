#!/usr/bin/env python3
"""Merge the per-paper files that reading helpers write into lrm.json.

    python3 merge_papers.py lrm.json --from helper_out/

Each helper writes one JSON file per paper into the folder (one paper object,
or a list of them), in the lrm.json paper format. This adds each to the "papers"
list of lrm.json. A paper that has the same "id" (or DOI) is UPDATED with the reading
fields only (cells, evidence, quote lists, type, source_basis); its authors, year, title, journal,
volume, issue, pages, DOI, ISSN, quartile, Crossref status and notices are kept. Creates
lrm.json if it does not exist. It exists so the chat never has to re-type
the helpers' output: that costs output tokens and is a chance to change a word.

A file that is not valid JSON, or has no "id" or DOI, is reported and skipped;
nothing else in lrm.json is touched.
"""

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import json
import os
import sys

from common import clean_doi, fold, scrub


# Fields a reading helper's file must never overwrite on a paper that is already in lrm.json.
KEEP = {"authors", "year", "title", "journal", "volume", "issue", "pages", "doi", "issn", "quartile",
        "crossref", "notices", "id"}


def key(p):
    return fold(p.get("id") or clean_doi(p.get("doi")) or "")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lrm")
    ap.add_argument("--from", dest="src", required=True, help="folder of per-paper .json files")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.src):
        print(f"Error: {a.src} is not a folder", file=sys.stderr)
        return 1
    data = {"papers": []}
    if os.path.exists(a.lrm):
        try:
            data = json.load(open(a.lrm, encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"Error: {a.lrm} is not valid JSON ({e})", file=sys.stderr)
            return 1
    data.setdefault("papers", [])
    index = {key(p): i for i, p in enumerate(data["papers"]) if key(p)}
    added = replaced = bad = 0
    for name in sorted(os.listdir(a.src)):
        if not name.lower().endswith(".json"):
            continue
        path = os.path.join(a.src, name)
        try:
            obj = scrub(json.load(open(path, encoding="utf-8")))
        except (json.JSONDecodeError, OSError) as e:
            print(f"SKIPPED {name}: not valid JSON ({e})", file=sys.stderr)
            bad += 1
            continue
        for p in obj if isinstance(obj, list) else [obj]:
            k = key(p) if isinstance(p, dict) else ""
            if not k:
                print(f'SKIPPED {name}: a paper has no "id" or DOI', file=sys.stderr)
                bad += 1
            elif k in index:
                # Update, never replace: the paper already carries its Crossref-checked citation,
                # quartile and notices, and a reading helper's file does not hold those.
                cur = data["papers"][index[k]]
                cur.update({f: v for f, v in p.items() if f not in KEEP})
                replaced += 1
            else:
                index[k] = len(data["papers"])
                data["papers"].append(p)
                added += 1
    with open(a.lrm, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print(f"{a.lrm}: {added} added, {replaced} replaced, {bad} skipped; {len(data['papers'])} papers in total")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
