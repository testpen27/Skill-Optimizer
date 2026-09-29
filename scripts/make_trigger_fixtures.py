#!/usr/bin/env python3
"""Build evals/trigger-fixtures/ from the skill's own synthetic exports.

    python3 scripts/make_trigger_fixtures.py

Trigger queries say things like "the three studio exports I dropped in", so
each probe run needs plausible files for the months the queries name. The
skill ships only one August export per platform (plus June-August for
Facebook). Plain copies of those are byte-identical, and the model rightly
stops to point that out instead of loading the skill -- a harness artifact
that scored a direct "produce the Q3 YouTube report" request 1/10. So each
derived month gets its own dates and deterministically perturbed numbers.
"""

import calendar
import csv
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "skills" / "social-media-report" / "evals" / "fixtures"
OUT = ROOT / "evals" / "trigger-fixtures"

COPIED = ["facebook_export_2026-06.csv", "facebook_export_2026-07.csv",
          "facebook_export_2026-08.csv", "facebook_segments_2026-08.csv"]
DERIVED = {
    "instagram_export_2026-08.csv": ("instagram_insights", ["2026-07", "2026-08", "2026-09"]),
    "tiktok_export_2026-08.csv": ("tiktok_analytics", ["2026-08", "2026-09"]),
    "youtube_export_2026-08.csv": ("youtube_studio", ["2026-08", "2026-09", "2026-10"]),
}


def _num(value, factor, rng):
    try:
        x = float(value)
    except ValueError:
        return value
    y = x * factor * rng.uniform(0.9, 1.1)
    return str(round(y)) if "." not in value else f"{y:.1f}"


def derive(src: Path, month: str, seed: int):
    with src.open(newline="") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]
    year, mon = map(int, month.split("-"))
    days = calendar.monthrange(year, mon)[1]
    rng = random.Random(seed)
    factor = rng.uniform(0.8, 1.2)
    out = [header]
    for day in range(1, days + 1):
        base = body[(day - 1) % len(body)]
        out.append([f"{month}-{day:02d}"] + [_num(v, factor, rng) for v in base[1:]])
    return out


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name in COPIED:
        shutil.copy(SRC / name, OUT / name)
    for seed, (src, (prefix, months)) in enumerate(DERIVED.items()):
        for i, month in enumerate(months):
            rows = derive(SRC / src, month, seed * 100 + i)
            with (OUT / f"{prefix}_{month}.csv").open("w", newline="") as f:
                csv.writer(f).writerows(rows)
    print("\n".join(sorted(p.name for p in OUT.iterdir())))


if __name__ == "__main__":
    main()
