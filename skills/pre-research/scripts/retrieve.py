#!/usr/bin/env python3
"""Download the legally free papers from a records file and keep a manifest.

Standard library only. Subcommands:

  download records.json --dest DIR [--max 50] [--only-new]
      Downloads every record that has an open-access copy (from `openalex.py
      enrich` or `list`). Respects robots.txt, waits between requests to the
      same site, and keeps a file only if it really is a PDF. Records without a
      free copy are listed as "paywalled" for the user to fetch through their
      own library access. Writes DIR/manifest.json.

  adopt DIR/manifest.json --file PATH --doi DOI
      Files a PDF the user downloaded themselves (for example from a paywalled
      publisher page) into DIR under the standard name and marks it retrieved.

  status DIR/manifest.json
      Prints the counts and the paywalled list.

It never logs in, never uses the user's library session, and never touches
paywalled publisher pages: those are the user's to download.
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

UA = "research-search-string/1.0 (open-access download for a literature review)"
DELAY = float(os.environ.get("RETRIEVE_DELAY", "2"))  # seconds between requests to one site
MIN_BYTES = 1000


class Fail(Exception):
    pass


def safe_name(rec):
    first = (rec.get("authors") or ["Unknown"])[0]
    # "Rokhani, Zaiemilia Mohd" or "Zaiemilia Mohd Rokhani": take the surname.
    surname = first.split(",")[0] if "," in first else first.split()[-1] if first.split() else "Unknown"
    words = re.findall(r"[A-Za-z0-9]+", unicodedata.normalize("NFKD", rec.get("title") or "untitled"))
    text = f"{surname}_{rec.get('year') or 'nd'}_{'_'.join(words[:6])}"
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9_\-]", "", text)[:120] + ".pdf"


def unique_path(dest, name):
    path = os.path.join(dest, name)
    stem, ext = os.path.splitext(path)
    n = 2
    while os.path.exists(path):
        path = f"{stem}_{n}{ext}"
        n += 1
    return path


class Fetcher:
    """Polite downloader: robots.txt per site, a delay per site, PDF check."""

    def __init__(self, delay=DELAY):
        self.delay = delay
        self.robots = {}
        self.last = {}

    def allowed(self, url):
        parts = urllib.parse.urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                req = urllib.request.Request(base + "/robots.txt", headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=20) as r:
                    rp.parse(r.read().decode("utf-8", "replace").splitlines())
            except urllib.error.HTTPError as e:
                # No robots.txt (404) means no restrictions; 401/403 means stay out.
                rp.parse([] if e.code == 404 else ["User-agent: *", "Disallow: /"])
            except Exception:
                rp.parse([])
            self.robots[base] = rp
        return self.robots[base].can_fetch(UA, url)

    def wait(self, url):
        host = urllib.parse.urlsplit(url).netloc
        gap = time.time() - self.last.get(host, 0)
        if gap < self.delay:
            time.sleep(self.delay - gap)
        self.last[host] = time.time()

    def get_pdf(self, url):
        if not self.allowed(url):
            raise Fail("robots.txt does not allow automated download from this site")
        self.wait(url)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/pdf,*/*;q=0.5"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read(60_000_000)
                ctype = r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            raise Fail(f"HTTP {e.code}")
        except Exception as e:
            raise Fail(f"download failed ({e.__class__.__name__})")
        if not data.startswith(b"%PDF-"):
            kind = "a web page" if b"<html" in data[:2000].lower() or "html" in ctype else "not a PDF"
            raise Fail(f"the link returned {kind}, not the paper (often a landing page or a bot check)")
        if len(data) < MIN_BYTES or b"%%EOF" not in data[-4096:]:
            raise Fail("the PDF is incomplete or truncated")
        return data


def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        raise Fail(f"cannot find {path}")
    except json.JSONDecodeError as e:
        raise Fail(f"{path} is not valid JSON ({e})")


def save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def cmd_download(args, fetcher=None):
    fetcher = fetcher or Fetcher()
    recs = load(args.records)["records"]
    os.makedirs(args.dest, exist_ok=True)
    mpath = os.path.join(args.dest, "manifest.json")
    manifest = load(mpath) if os.path.exists(mpath) else {"items": []}
    done = {i["key"]: i for i in manifest["items"]}
    tried = 0
    for r in recs:
        key = ("doi:" + r["doi"]) if r.get("doi") else "title:" + (r.get("title") or "")
        prev = done.get(key)
        if prev and prev["status"] in ("downloaded", "downloaded by user"):
            continue
        item = {"key": key, "doi": r.get("doi", ""), "title": r.get("title", ""), "year": r.get("year"),
                "authors": r.get("authors", [])[:3], "publisher": r.get("publisher", ""),
                "venue": r.get("venue", ""), "landing_url": r.get("landing_url", ""),
                "status": "", "file": "", "source_url": "", "license": r.get("license", ""), "reason": ""}
        urls = [u for u in (r.get("pdf_url"), r.get("oa_url")) if u]
        if not r.get("is_oa") or not urls:
            item["status"] = "paywalled" if r.get("is_oa") is False or not urls else "no free copy found"
            item["reason"] = "no legal free copy found; download it through your library access"
        elif tried >= args.max:
            item["status"] = "skipped"
            item["reason"] = f"over the limit of {args.max} downloads for this run"
        else:
            tried += 1
            errors = []
            for u in dict.fromkeys(urls):
                try:
                    data = fetcher.get_pdf(u)
                    path = unique_path(args.dest, safe_name(r))
                    with open(path, "wb") as f:
                        f.write(data)
                    item.update(status="downloaded", file=os.path.basename(path), source_url=u, reason="")
                    break
                except Fail as e:
                    errors.append(f"{u}: {e}")
            if item["status"] != "downloaded":
                item["status"] = "failed"
                item["reason"] = " | ".join(errors)
        done[key] = item
        print(f"{item['status']:>18}  {(item['title'] or '')[:70]}")
    manifest["items"] = list(done.values())
    manifest["updated"] = time.strftime("%Y-%m-%d %H:%M")
    save(mpath, manifest)
    summary(manifest)


def cmd_adopt(args):
    manifest = load(args.manifest)
    doi = args.doi.lower().replace("https://doi.org/", "")
    item = next((i for i in manifest["items"] if i.get("doi") == doi), None)
    if item is None:
        raise Fail(f"no record with DOI {doi} in the manifest")
    if item["status"].startswith("downloaded") and not args.replace:
        raise Fail(f"{doi} is already filed as {item['file']}; pass --replace to swap in this file")
    data = open(args.file, "rb").read()
    if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-4096:]:
        raise Fail(f"{args.file} is not a complete PDF (it may be a saved web page or an unfinished download)")
    dest = os.path.dirname(os.path.abspath(args.manifest))
    if item.get("file") and os.path.exists(os.path.join(dest, item["file"])):
        os.remove(os.path.join(dest, item["file"]))
    path = unique_path(dest, safe_name(item))
    shutil.copyfile(args.file, path)
    if args.move:
        os.remove(args.file)
    item.update(status="downloaded by user", file=os.path.basename(path), reason="")
    save(args.manifest, manifest)
    print(f"filed {os.path.basename(path)}")


def summary(manifest):
    counts = {}
    for i in manifest["items"]:
        counts[i["status"]] = counts.get(i["status"], 0) + 1
    print("\n" + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))


def cmd_status(args):
    manifest = load(args.manifest)
    summary(manifest)
    for i in manifest["items"]:
        if i["status"] in ("paywalled", "no free copy found", "failed"):
            print(f"- [{i['status']}] {i['title'][:80]}  {('https://doi.org/' + i['doi']) if i['doi'] else i['landing_url']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("download"); p.add_argument("records"); p.add_argument("--dest", required=True)
    p.add_argument("--max", type=int, default=50); p.set_defaults(fn=cmd_download)
    p = sub.add_parser("adopt"); p.add_argument("manifest"); p.add_argument("--file", required=True)
    p.add_argument("--doi", required=True); p.add_argument("--move", action="store_true")
    p.add_argument("--replace", action="store_true"); p.set_defaults(fn=cmd_adopt)
    p = sub.add_parser("status"); p.add_argument("manifest"); p.set_defaults(fn=cmd_status)
    args = ap.parse_args(argv)
    try:
        args.fn(args)
    except Fail as e:
        print("Error:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
