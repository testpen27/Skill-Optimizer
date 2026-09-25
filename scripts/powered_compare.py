#!/usr/bin/env python3
"""Directly compare two skill descriptions at a higher, trustworthy runs-per-query.

Two problems with just cranking up --runs-per-query on the stock run_loop:

1. It still uses run_loop's iterative "propose a new description" step, which
   we don't want here -- we have two specific candidates and want to know
   which one is actually better, not have a third invented.

2. Upstream scripts.run_eval.run_eval() catches any exception from a worker
   (including trigger_probe.ProbeFailure -- a timeout, a crash, a run that
   never produced a real turn) and silently records it as `False` ("did not
   trigger"), mixed in with genuine non-triggers. trigger_probe.py's own
   docstring says a ProbeFailure "says nothing about triggering" and must not
   be counted as a zero -- but nothing enforces that once run_eval.py's own
   try/except gets to it first. At a 90s timeout roughly 1 in 6 runs failed
   this way in the first belanjawan-brain pass, which would quietly depress
   whichever candidate happened to draw more timeouts.

This script calls trigger_probe.run_single_query directly, retries a failed
run (up to --max-retries times) instead of counting it as a non-trigger, and
reports how many runs were unrecoverable so that's visible rather than
silently folded into the trigger rate.
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

SKILL_CREATOR = os.environ.get("SKILL_CREATOR")
if not SKILL_CREATOR:
    sys.exit("Set SKILL_CREATOR to the skill-creator skill directory")
sys.path.insert(0, SKILL_CREATOR)

from scripts.run_eval import find_project_root  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from trigger_probe import ProbeFailure, run_single_query  # noqa: E402


def run_one(query, skill_name, description, timeout, project_root, model):
    try:
        return run_single_query(query, skill_name, description, timeout, project_root, model)
    except ProbeFailure as e:
        return str(e)  # sentinel: any str means "failed", any bool means a real result


def evaluate(eval_set, skill_name, description, runs_per_query, num_workers, timeout, project_root, model, max_retries):
    per_query = {item["query"]: {"item": item, "runs": [], "unrecoverable_failures": []} for item in eval_set}

    def submit(executor, query, n):
        return [
            executor.submit(run_one, query, skill_name, description, timeout, str(project_root), model)
            for _ in range(n)
        ]

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        pending = {}
        for item in eval_set:
            for f in submit(executor, item["query"], runs_per_query):
                pending[f] = (item["query"], 0)

        while pending:
            done = list(as_completed(list(pending.keys())))
            for f in done:
                query, retry_count = pending.pop(f)
                result = f.result()
                if isinstance(result, bool):
                    per_query[query]["runs"].append(result)
                else:
                    if retry_count < max_retries:
                        print(f"  retry ({retry_count + 1}/{max_retries}) after: {result[:100]}", file=sys.stderr, flush=True)
                        nf = executor.submit(run_one, query, skill_name, description, timeout, str(project_root), model)
                        pending[nf] = (query, retry_count + 1)
                    else:
                        print(f"  unrecoverable after {max_retries} retries: {result[:100]}", file=sys.stderr, flush=True)
                        per_query[query]["unrecoverable_failures"].append(result)

    results = []
    for query, data in per_query.items():
        runs = data["runs"]
        n = len(runs)
        t = sum(runs)
        should_trigger = data["item"]["should_trigger"]
        rate = t / n if n else None
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "triggers": t,
            "runs": n,
            "trigger_rate": rate,
            "unrecoverable_failures": len(data["unrecoverable_failures"]),
            "pass": (rate is not None) and ((rate >= 0.5) if should_trigger else (rate < 0.5)),
        })
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--candidate", action="append", required=True, help="LABEL=path/to/description.txt")
    parser.add_argument("--runs-per-query", type=int, default=10)
    parser.add_argument("--num-workers", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=150)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    project_root = find_project_root()

    output = {}
    for spec in args.candidate:
        label, path = spec.split("=", 1)
        description = Path(path).read_text()
        print(f"\n=== {label} ({args.runs_per_query} runs/query, {len(eval_set)} queries, timeout={args.timeout}s) ===", file=sys.stderr, flush=True)
        t0 = time.time()
        results = evaluate(
            eval_set, args.skill_name, description,
            args.runs_per_query, args.num_workers, args.timeout, project_root, args.model, args.max_retries,
        )
        elapsed = time.time() - t0

        tp = fn = fp = tn = 0
        total_unrecoverable = 0
        for r in results:
            total_unrecoverable += r["unrecoverable_failures"]
            if r["should_trigger"]:
                tp += r["triggers"]
                fn += (r["runs"] - r["triggers"])
            else:
                fp += r["triggers"]
                tn += (r["runs"] - r["triggers"])
        recall = [tp, tp + fn]
        false_fires = [fp, fp + tn]

        output[label] = {
            "description": description,
            "elapsed_s": round(elapsed, 1),
            "recall": recall,
            "false_fires": false_fires,
            "unrecoverable_failures": total_unrecoverable,
            "results": results,
        }
        Path(args.out).write_text(json.dumps(output, indent=2))
        print(
            f"{label} done in {elapsed:.0f}s: recall {recall[0]}/{recall[1]}, "
            f"false_fires {false_fires[0]}/{false_fires[1]}, unrecoverable_failures={total_unrecoverable}",
            file=sys.stderr, flush=True,
        )

    Path(args.out).write_text(json.dumps(output, indent=2))
    print(f"\nSaved to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
