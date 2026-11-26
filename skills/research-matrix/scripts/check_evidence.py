#!/usr/bin/env python3
"""Check every LRM cell against the quotes it was written from, and every quote
against the paper text it was taken from.

    python3 check_evidence.py lrm.json --papers PAPERS_DIR

Each paper in lrm.json carries, per text column, the verbatim quotes the cell
was written from:

    "source_basis": "full text",            # or "partial" / "abstract only"
    "evidence": {
      "results": [{"q": "Teachers who used the app scored higher (p = .03)",
                   "loc": "Results, p. 7"}],
      ...
    }

and PAPERS_DIR holds the text that was read, one file per paper named after
its "id" (or its DOI with "/" replaced by "_"): <id>.txt or <id>.md.

"overclaims" (abstract claims more than the body) are checked too: both quotes
must be in the saved text, and no number may reach the cell from the abstract's
claim alone.

ERROR (exit 1), fix by cutting or narrowing the cell, never by adding:
  - a filled cell with no quotes;
  - a quote that is not in the paper's saved text (misquoted or invented);
    "..." inside a quote skips words, the pieces must appear in order;
  - a number in a cell that none of the paper's quotes contains
    (numbers are never computed, rounded or converted);
  - no saved text for a paper that has quotes.
WARN:
  - a column's quote is hedged ("may", "suggest", ...) and its cell is not;
  - a cell uses causal wording ("leads to", "improves", ...) its quotes do not;
  - no source_basis recorded for the paper.
"""

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import json
import os
import re
import sys
import unicodedata

from common import clean_doi, scrub

TEXT_FIELDS = ["introduction", "methodology", "theory", "results", "discussion"]
BASES = {"full text", "partial", "abstract only"}
HEDGES = re.compile(r"\b(may|might|could|suggests?|suggested|appears?|appeared|possibly|"
                    r"likely|tentative(?:ly)?|preliminary|seems?)\b", re.I)
CAUSAL = re.compile(r"\b(caus(?:e|es|ed|ing)|leads? to|led to|results? in|resulted in|due to|because of|"
                    r"effects? of|impacts? (?:on|of)|improv(?:e|es|ed)|increas(?:e|es|ed)|"
                    r"reduc(?:e|es|ed)|drives?|drove)\b", re.I)
NUMBER = re.compile(r"(?<![\w.])(?:\d[\d,]*(?:\.\d+)?|\.\d+)")


def norm(s):
    """Lower-case, NFKC (ligatures), unify quotes and dashes, join words broken
    across lines by a hyphen, drop soft hyphens, collapse whitespace."""
    s = unicodedata.normalize("NFKC", s or "").replace("­", "")
    s = re.sub(r"[‘’‚‛′]", "'", s)
    s = re.sub(r"[“”„‟″]", '"', s)
    s = re.sub(r"[‐-―−]", "-", s)
    s = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def squash(s):
    """The comparison form of a text: normalised, then with whitespace, markdown
    emphasis marks (_ and *) and backslash escapes removed. Text taken from a web
    page keeps '_n_' and '\\[' where a reader quotes 'n' and '['; a PDF has line
    and column breaks. None of that is a wrong quote."""
    return re.sub(r"[\s_*\\]", "", norm(s))


def quote_found(quote, text_sq):
    """Every '...'-separated piece of the quote appears in the text, in order.
    text_sq must be squash(text)."""
    pos = 0
    for piece in re.split(r"\s*(?:\.\.\.|\u2026)\s*", norm(quote)):
        piece = squash(piece.strip(" .,;:"))
        if not piece:
            continue
        i = text_sq.find(piece, pos)
        if i < 0:
            return False
        pos = i + len(piece)
    return True


def numbers(s):
    """Numbers as written, normalised only so the same value matches: '1,234' ->
    '1234', '.03' -> '0.03'. No rounding: 0.031 and 0.03 stay different."""
    out = set()
    for n in NUMBER.findall(s or ""):
        n = n.replace(",", "")
        out.add("0" + n if n.startswith(".") else n)
    return out


def paper_text(papers_dir, p):
    keys = [k for k in (p.get("id"), clean_doi(p.get("doi")).replace("/", "_") if p.get("doi") else None) if k]
    try:
        names = os.listdir(papers_dir)
    except OSError:
        return None, None
    for k in keys:
        for name in names:
            base, ext = os.path.splitext(name)
            if ext.lower() in (".txt", ".md") and base.lower() == k.lower():
                path = os.path.join(papers_dir, name)
                return open(path, encoding="utf-8", errors="replace").read(), path
    return None, None


def check(data, papers_dir):
    errors, warns = [], []
    for i, p in enumerate(data.get("papers") or [], 1):
        tag = f"paper {i} ({p.get('id') or (p.get('title') or 'untitled')[:30]})"
        ev = p.get("evidence") or {}
        if p.get("source_basis") not in BASES:
            warns.append(f"{tag}: no source_basis (full text / partial / abstract only)")
        quotes_all = []
        for f in TEXT_FIELDS:
            for item in ev.get(f) or []:
                quotes_all.append((f, item.get("q") if isinstance(item, dict) else str(item)))
        for kind in ("abstract_claims", "caveats"):          # the reader's exhaustive quote lists
            for item in p.get(kind) or []:
                quotes_all.append(("_" + kind, item.get("q") if isinstance(item, dict) else str(item)))
        over = p.get("overclaims") or []
        for oc in over:
            if oc.get("body") and oc.get("field") in TEXT_FIELDS:
                quotes_all.append((oc["field"], oc["body"]))
        text, path = paper_text(papers_dir, p) if (quotes_all or over) else (None, None)
        if quotes_all and text is None:
            errors.append(f"{tag}: no saved text in {papers_dir} named after its id or DOI; "
                          f"save the text that was read as <id>.txt")
        text_n = squash(text) if text else None
        all_nums = set()
        for f, q in quotes_all:
            if f != "_abstract_claims":      # body quotes (columns and caveats) back a cell's numbers; the abstract's claims never do
                all_nums |= numbers(q)
            if text_n is not None and not quote_found(q, text_n):
                errors.append(f"{tag} {f}: quote not found in {os.path.basename(path)}: \"{q[:90]}\"")
        for oc in over:
            a = oc.get("abstract") or ""
            if text_n is not None and a and not quote_found(a, text_n):
                errors.append(f"{tag}: overclaim's abstract quote not found in {os.path.basename(path)}: \"{a[:90]}\"")
            stray = numbers(a) - all_nums
            cell = p.get(oc.get("field")) or ""
            leaked = sorted(stray & numbers(cell))
            if leaked:
                errors.append(f"{tag} {oc.get('field')}: number(s) {', '.join(leaked)} come from the abstract's "
                              f"overclaim, not the body; write the body's figure")
        for f in TEXT_FIELDS:
            cell = (p.get(f) or "").strip()
            if not cell:
                continue
            qs = [q for ff, q in quotes_all if ff == f]
            if not qs:
                errors.append(f"{tag} {f}: filled cell has no quotes in evidence")
                continue
            missing = sorted(numbers(cell) - all_nums, key=lambda x: float(x))
            if missing:
                errors.append(f"{tag} {f}: number(s) {', '.join(missing)} in the cell are in none of the paper's quotes")
            joined = " ".join(qs)
            if HEDGES.search(joined) and not HEDGES.search(cell):
                h = HEDGES.search(joined).group(0)
                warns.append(f"{tag} {f}: the quote is hedged (\"{h}\") but the cell is not")
            for m in CAUSAL.finditer(cell):
                if not re.search(re.escape(m.group(0)), joined, re.I):
                    warns.append(f"{tag} {f}: causal wording \"{m.group(0)}\" is not in the quotes")
                    break
    return errors, warns


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lrm")
    ap.add_argument("--papers", required=True, help="folder holding the saved text of each paper")
    a = ap.parse_args(argv)
    try:
        data = scrub(json.load(open(a.lrm, encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    errors, warns = check(data, a.papers)
    for w in warns:
        print("WARN:  " + w)
    for e in errors:
        print("ERROR: " + e)
    n = len(data.get("papers") or [])
    print(f"{'FAILED' if errors else 'OK'}: {n} papers, {len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
