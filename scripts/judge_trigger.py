#!/usr/bin/env python3
"""Isolated trigger-judgment eval for the find-paper skill description.

Standard skill-creator trigger testing (nest `claude -p` with a synthetic
command file, watch for a Skill/Read tool_use) doesn't work in this
environment: this account has the identical "find-paper" skill already
installed as a marketplace plugin (anthropic-skills:find-paper), so nested
agentic sessions keep invoking that pre-existing skill instead of the
synthetic test double, regardless of what description is under test.

Instead, this asks a fresh, tool-less `claude -p` call to directly judge
"would Claude Code invoke a skill with this description for this query",
using the same heuristic Claude Code actually uses (skills trigger for
complex/specialized tasks, not one-step things it can do directly). This
avoids the environment's plugin collision because no real skill list or
tool-use loop is involved -- it's a pure classification call.
"""
import json
import os
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

JUDGE_PROMPT_TEMPLATE = """You are simulating how Claude Code decides whether to consult a specialized skill. Claude only consults a skill for tasks it cannot trivially handle on its own with basic tools -- simple one-step queries usually do NOT trigger a skill even if the description matches, while complex, multi-step, or specialized queries DO trigger it when the description matches.

Here is the ONLY available skill:
Name: {skill_name}
Description: {description}

User message: {query!r}

Would Claude Code invoke (trigger) this skill for this message? Answer with exactly one word: YES or NO."""


def judge_one(query: str, skill_name: str, description: str, model: str) -> bool:
    prompt = JUDGE_PROMPT_TEMPLATE.format(skill_name=skill_name, description=description, query=query)
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in (
            "CLAUDECODE",
            "CLAUDE_CODE_SESSION_ID",
            "CLAUDE_CODE_CHILD_SESSION",
            "CLAUDE_CODE_REMOTE_SESSION_ID",
        )
    }
    cmd = [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--model",
        model,
        "--session-id",
        str(uuid.uuid4()),
        "--no-session-persistence",
        "--tools",
        "",
    ]
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
        data = json.loads(proc.stdout)
        result = data.get("result", "").strip().upper()
        return result.startswith("YES")
    except Exception as e:
        print(f"ERROR judging query {query[:50]!r}: {e}", file=sys.stderr)
        return False


def run_eval(eval_set: list[dict], skill_name: str, description: str, model: str, workers: int = 8) -> dict:
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(judge_one, item["query"], skill_name, description, model): item
            for item in eval_set
        }
        for fut in as_completed(futures):
            item = futures[fut]
            triggered = fut.result()
            results.append(
                {
                    "query": item["query"],
                    "should_trigger": item["should_trigger"],
                    "triggered": triggered,
                    "pass": triggered == item["should_trigger"],
                }
            )
    total = len(results)
    passed = sum(r["pass"] for r in results)
    return {"description": description, "results": results, "accuracy": passed / total if total else 0.0, "passed": passed, "total": total}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", required=True)
    ap.add_argument("--skill-name", default="find-paper")
    ap.add_argument("--description", required=True, help="Path to a file containing the description, or the description text itself")
    ap.add_argument("--model", default="claude-sonnet-5")
    args = ap.parse_args()

    with open(args.eval_set) as f:
        eval_set = json.load(f)

    if os.path.isfile(args.description):
        with open(args.description) as f:
            description = f.read().strip()
    else:
        description = args.description

    out = run_eval(eval_set, args.skill_name, description, args.model)
    for r in sorted(out["results"], key=lambda r: r["pass"]):
        tag = "PASS" if r["pass"] else "FAIL"
        print(f"[{tag}] expected={r['should_trigger']!s:5} got={r['triggered']!s:5} {r['query'][:70]}")
    print(f"\nAccuracy: {out['passed']}/{out['total']} = {out['accuracy']:.0%}")
