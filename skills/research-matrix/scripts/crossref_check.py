#!/usr/bin/env python3
"""Check each paper's citation in lrm.json against its Crossref record.

    python3 crossref_check.py lrm.json [--offline DIR] [--apply] [--write]

For every paper with a DOI, compares authors (family names, in order), year,
title, journal, volume, issue and pages with Crossref, and prints what
differs. Crossref is treated as the record of truth for the citation.

  --offline DIR  read saved Crossref responses from DIR instead of the network.
                 Name each file after its DOI with "/" replaced by "_"
                 (10.1177_0002764213479369.json). The file can be the raw JSON
                 from https://api.crossref.org/works/<doi>, or a Firecrawl
                 scrape of that URL. Use this where the network is blocked.
  --apply        copy Crossref's authors, year, journal, volume, issue, pages
                 and ISSN into lrm.json (never the title: Crossref keeps the
                 publisher's capitalisation, APA 7 wants sentence case).
  --write        save the "crossref" status (verified / mismatch / unchecked)
                 and any filled-in fields back to lrm.json.

It also reads the record's retraction and correction notices (Crossref's
"updated-by" field, which includes the Retraction Watch database) and stores
them as "notices" on the paper, so the matrix can flag a retracted paper.
A paper with no notices gets an empty list: that is a checked "none found",
not a guarantee, since Retraction Watch is most complete for retractions and
less so for corrections.

Nothing is guessed: a paper with no DOI, or no response, stays "unchecked".
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from common import author_string, clean_doi, dash, fold, load_json_loose, read_text, strip_markup

UA = "research-matrix/1.0 (academic citation check)"


def offline_path(directory, doi):
    """Find the saved response for a DOI. DOIs are case-insensitive, so the file
    name is matched without regard to case."""
    stem = fold(doi.replace("/", "_"))
    try:
        names = os.listdir(directory)
    except OSError:
        return None
    for ext in (".json", ".md", ".txt"):
        for name in names:
            base, e = os.path.splitext(name)
            if e.lower() == ext and fold(base) == stem:
                return os.path.join(directory, name)
    return None


def fetch(doi, offline=None):
    """Return the Crossref 'message' dict, or (None, reason)."""
    if offline:
        path = offline_path(offline, doi)
        if not path:
            return None, f"no saved response for {doi} in {offline}"
        data = load_json_loose(read_text(path))
    else:
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/()")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = load_json_loose(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return None, f"Crossref answered HTTP {e.code} for {doi}"
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            return None, f"cannot reach Crossref ({e}); fetch the URL another way and use --offline"
    if not isinstance(data, dict) or "message" not in data:
        return None, f"could not read a Crossref record for {doi}"
    return data["message"], None


def print_year(msg):
    for key in ("published-print", "issued", "published-online", "published"):
        parts = (msg.get(key) or {}).get("date-parts") or [[None]]
        if parts and parts[0] and parts[0][0]:
            return int(parts[0][0]), key
    return None, None


def years_in(msg):
    ys = set()
    for key in ("published-print", "issued", "published-online", "published"):
        parts = (msg.get(key) or {}).get("date-parts") or [[None]]
        if parts and parts[0] and parts[0][0]:
            ys.add(int(parts[0][0]))
    return ys


def crossref_authors(msg):
    out = []
    for a in msg.get("author") or []:
        if a.get("family"):
            out.append(author_string(strip_markup(a["family"]), strip_markup(a.get("given") or "")))
        elif a.get("name"):
            out.append(strip_markup(a["name"]))
    return out


def crossref_title(msg):
    title = strip_markup((msg.get("title") or [""])[0])
    sub = strip_markup((msg.get("subtitle") or [""])[0])
    return title, (f"{title}: {sub}" if sub else title)


def crossref_notices(msg):
    """Retractions, corrections and similar notices on this paper's record."""
    out = []
    for u in msg.get("updated-by") or []:
        when = ((u.get("updated") or {}).get("date-time") or "")[:10]
        out.append({"type": (u.get("type") or "").lower(), "date": when,
                    "source": u.get("source") or "", "doi": u.get("DOI") or ""})
    return sorted(out, key=lambda n: n["date"])


def compare(paper, msg):
    """List of (field, ours, crossref) that differ."""
    diffs = []
    ours = [fold(a.split(",")[0]) for a in paper.get("authors") or []]
    theirs = [fold(a.split(",")[0]) for a in crossref_authors(msg)]
    if theirs and ours != theirs:
        diffs.append(("authors", "; ".join(paper.get("authors") or []), "; ".join(crossref_authors(msg))))
    ys = years_in(msg)
    if ys and str(paper.get("year")) not in {str(y) for y in ys}:
        diffs.append(("year", paper.get("year"), "/".join(str(y) for y in sorted(ys))))
    short, full = crossref_title(msg)
    # Publishers prefix a retracted paper's title with "RETRACTED:"; that is a flag, not the title.
    short, full = (re.sub(r"^\s*retracted\s*[:\-]?\s*", "", t, flags=re.I) for t in (short, full))
    mine = fold(re.sub(r"^\s*retracted\s*[:\-]?\s*", "", paper.get("title") or "", flags=re.I))
    if mine and short and mine not in {fold(short), fold(full)}:
        diffs.append(("title", paper.get("title"), full))
    journal = strip_markup((msg.get("container-title") or [""])[0])
    if journal and fold(paper.get("journal")).replace(" and ", " ") != fold(journal).replace(" and ", " "):
        diffs.append(("journal", paper.get("journal"), journal))
    for field, key in (("volume", "volume"), ("issue", "issue")):
        theirs_v = str(msg.get(key) or "").strip()
        if theirs_v and str(paper.get(field) or "").strip() != theirs_v:
            diffs.append((field, paper.get(field), theirs_v))
    pg = msg.get("page")
    if pg and paper.get("pages") and dash(str(paper["pages"])) != dash(pg):
        diffs.append(("pages", paper.get("pages"), pg))
    return diffs


def apply_record(paper, msg):
    """Copy Crossref's citation fields into the paper. Returns what changed."""
    changed = []
    year, _ = print_year(msg)
    new = {
        "authors": crossref_authors(msg) or None,
        "year": year,
        "journal": strip_markup((msg.get("container-title") or [""])[0]) or None,
        "volume": msg.get("volume"),
        "issue": msg.get("issue"),
        "pages": dash(msg["page"]) if msg.get("page") else None,
        "issn": (msg.get("ISSN") or [None])[0],
    }
    for k, v in new.items():
        if v and paper.get(k) != v:
            changed.append(k)
            paper[k] = v
    return changed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lrm")
    ap.add_argument("--offline")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    data = json.load(open(a.lrm, encoding="utf-8"))
    bad = 0
    for i, p in enumerate(data["papers"], 1):
        doi = clean_doi(p.get("doi"))
        tag = f"[{i}] {(p.get('title') or 'untitled')[:55]}"
        if not doi:
            p["crossref"] = "unchecked"
            print(f"{tag}\n    no DOI, so not checked")
            continue
        msg, why = fetch(doi, a.offline)
        if msg is None:
            p["crossref"] = "unchecked"
            print(f"{tag}\n    unchecked: {why}")
            continue
        diffs = compare(p, msg)
        p["notices"] = crossref_notices(msg)
        for n in p["notices"]:
            print(f"{tag}\n    NOTICE: {n['type'] or 'update'} {n['date']} (source: {n['source'] or 'publisher'})")
        if a.apply:
            changed = apply_record(p, msg)
            if changed:
                print(f"{tag}\n    updated from Crossref: {', '.join(changed)}")
        elif not p.get("issn") and msg.get("ISSN"):
            p["issn"] = msg["ISSN"][0]
        if diffs and not a.apply:
            p["crossref"] = "mismatch"
            bad += 1
            print(f"{tag}\n    MISMATCH with Crossref:")
            for field, mine, theirs in diffs:
                print(f"      {field}: yours={mine!r}  crossref={theirs!r}")
        else:
            left = [d for d in compare(p, msg)]
            if left:  # only the title can remain after --apply
                p["crossref"] = "mismatch"
                bad += 1
                print(f"{tag}\n    MISMATCH remains: " + "; ".join(f"{f}: {m!r} vs {t!r}" for f, m, t in left))
            else:
                p["crossref"] = "verified"
                print(f"{tag}\n    verified against Crossref")
    if a.write:
        with open(a.lrm, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        print(f"Saved statuses to {a.lrm}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
