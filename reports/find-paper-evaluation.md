# find-paper description optimization

## Result: no change made — description already scores 100%

The `find-paper` skill's current description was tested against 30 realistic
trigger queries (10 should-trigger / 10 should-not-trigger in
`evals/find-paper-trigger-eval.json`, plus 10 harder edge cases in
`evals/find-paper-trigger-eval-round2-hard.json`, including direct competition with a generic
"deep research" skill and near-miss journal/citation questions). It scored
**30/30 (100%)** — every should-trigger query fired and every near-miss
correctly did not. See `results/find-paper/eval-v0-result.txt` and `results/find-paper/eval-v0-round2-result.txt`.

Given that, no description rewrite was applied — the existing frontmatter in
`skills/find-paper/SKILL.md` is unchanged.

## Why the standard skill-creator loop wasn't used as-is

`skill-creator`'s built-in `scripts/run_loop.py` / `run_eval.py` spawns nested
`claude -p` processes and watches for a `Skill`/`Read` tool_use naming a
synthetic test command, to measure whether a *candidate* description would
trigger. In this environment that approach was unreliable for two reasons,
both diagnosed and confirmed via manual reproduction:

1. **Session leakage.** `CLAUDE_CODE_SESSION_ID` (and related env vars) leak
   into the nested `claude -p` subprocess, so it attaches to the *parent's*
   live session instead of running as an independent, isolated session —
   it was literally continuing this conversation rather than evaluating the
   query fresh. Fixed locally by stripping those env vars and passing
   `--session-id <fresh-uuid> --no-session-persistence`.
2. **Marketplace collision (the blocker).** This account already has the
   identical skill installed as a plugin (`anthropic-skills:find-paper`).
   Even with the session-leak fixed, every nested run invoked the
   *pre-installed* plugin skill instead of the synthetic test command with
   the candidate description — because they're the same skill, Claude
   reasonably picks the real one. This makes the tool-invocation-based
   trigger test fundamentally unable to isolate "does *this candidate
   description* trigger" in this account.

`scripts/judge_trigger.py` works around this by asking a fresh, tool-less `claude -p`
call to directly judge "would Claude Code invoke a skill with this
description for this query", using the same trigger heuristic Claude Code
itself follows. No real skill list or tool-use loop is involved, so the
marketplace collision never comes into play. This is what actually produced
the 100% scores above.

## Files
- `evals/find-paper-trigger-eval.json`, `evals/find-paper-trigger-eval-round2-hard.json` — the 30 eval queries
- `scripts/judge_trigger.py` — the isolated judgment-based eval harness
- `evals/find-paper-orig-desc.txt` — the description tested (unchanged from shipped skill)
- `results/find-paper/eval-v0-result.txt`, `results/find-paper/eval-v0-round2-result.txt` — raw per-query results
