#!/usr/bin/env python3
"""Score several candidate descriptions on one eval set, head to head.

    PROBE_FIXTURES=evals/trigger-fixtures python3 scripts/compare_descriptions.py \
        --candidates evals/social-media-report-candidates.json \
        --eval-set evals/social-media-report-comparison.json \
        --out results/social-media-report/comparison.json \
        --model claude-sonnet-5 --runs-per-query 10

Cheaper than a full run_loop pass when only a few descriptions are in
question: no train/test split, no proposal calls, just skill-creator's
run_eval on each candidate with the same probe as run_loop_with_fixtures.py
(fixtures in each run's project root, early stop once the skill is invoked).
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_loop_with_fixtures  # noqa: E402,F401  patches trigger_probe
from trigger_probe import run_single_query  # noqa: E402

sys.path.insert(0, str(HERE.parent / "skill-creator"))
import scripts.run_eval as run_eval_mod  # noqa: E402

run_eval_mod.run_single_query = run_single_query


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True, help="JSON object {label: description}")
    ap.add_argument("--eval-set", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skill-name", default="social-media-report")
    ap.add_argument("--model", required=True)
    ap.add_argument("--runs-per-query", type=int, default=10)
    ap.add_argument("--num-workers", type=int, default=10)
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    candidates = json.loads(Path(args.candidates).read_text())
    eval_set = json.loads(Path(args.eval_set).read_text())
    out_path = Path(args.out)
    results = json.loads(out_path.read_text()) if out_path.exists() else {}

    for label, description in candidates.items():
        if label in results:
            print(f"{label}: already scored, skipping", file=sys.stderr)
            continue
        print(f"\n=== {label} ===", file=sys.stderr, flush=True)
        output = run_eval_mod.run_eval(
            eval_set=eval_set,
            skill_name=args.skill_name,
            description=description,
            num_workers=args.num_workers,
            timeout=args.timeout,
            project_root=Path.cwd(),
            runs_per_query=args.runs_per_query,
            model=args.model,
        )
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            print(f"  [{status}] rate={r['triggers']}/{r['runs']} expected={r['should_trigger']}: "
                  f"{r['query'][:70]}", file=sys.stderr, flush=True)
        s = output["summary"]
        print(f"{label}: {s['passed']}/{s['total']} passed", file=sys.stderr, flush=True)
        results[label] = output
        # Save after each candidate so a spend-limit abort keeps what was scored.
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
